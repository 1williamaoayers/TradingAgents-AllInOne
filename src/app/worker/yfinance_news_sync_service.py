"""
YFinance新闻同步服务
专门用于通过yfinance获取自选股的个股新闻并存入数据库
"""
import asyncio
import logging
import yfinance as yf
from typing import List, Dict, Any
from datetime import datetime, timezone

from app.core.database import get_mongo_db
from app.services.news_data_service import get_news_data_service

logger = logging.getLogger(__name__)

class YFinanceNewsSyncService:
    """YFinance新闻同步服务"""

    def __init__(self):
        self.db = None
        self.news_service = None

    async def initialize(self):
        """初始化服务"""
        self.db = get_mongo_db()
        self.news_service = await get_news_data_service()
        logger.info("✅ YFinance新闻同步服务已初始化")

    async def sync_favorites_news(self) -> Dict[str, Any]:
        """
        同步所有自选股的YFinance新闻
        """
        logger.info("🔄 开始同步自选股YFinance新闻...")
        
        stats = {
            "total_processed": 0,
            "success_count": 0,
            "error_count": 0,
            "news_count": 0,
            "start_time": datetime.utcnow()
        }

        try:
            # 1. 获取自选股列表
            symbols = await self._get_favorite_stocks()
            if not symbols:
                logger.warning("⚠️ 没有找到自选股")
                return stats
            
            stats["total_processed"] = len(symbols)
            logger.info(f"📊 需处理自选股: {len(symbols)} 只")

            # 2. 遍历同步 (串行或小并发，避免被封)
            # yfinance通常对并发比较敏感，建议串行或极小并发
            for symbol in symbols:
                try:
                    news_count = await self._sync_single_stock(symbol)
                    stats["success_count"] += 1
                    stats["news_count"] += news_count
                    if news_count > 0:
                        logger.info(f"  ✅ {symbol}: 获取 {news_count} 条新闻")
                except Exception as e:
                    stats["error_count"] += 1
                    logger.error(f"  ❌ {symbol}: 同步失败 - {e}")
                
                # 礼貌性延迟
                await asyncio.sleep(1.0)

            stats["end_time"] = datetime.utcnow()
            duration = (stats["end_time"] - stats["start_time"]).total_seconds()
            
            logger.info(f"🎉 YFinance新闻同步完成: 成功 {stats['success_count']}/{len(symbols)}, "
                        f"新增新闻 {stats['news_count']} 条, 耗时 {duration:.1f}s")
            
            return stats

        except Exception as e:
            logger.error(f"❌ YFinance同步总流程失败: {e}")
            return stats

    async def _get_favorite_stocks(self) -> List[str]:
        """获取去重后的自选股代码"""
        try:
            favorites_docs = await self.db.user_favorites.find(
                {}, {"favorites": 1, "_id": 0}
            ).to_list(None)
            
            codes = set()
            for doc in favorites_docs:
                for fav in doc.get("favorites", []):
                    code = fav.get("stock_code")
                    if code:
                        # yfinance需要正确的后缀
                        # 0700 -> 0700.HK, 01810 -> 01810.HK
                        
                        # 简单标准化处理
                        if code.isdigit() and len(code) >= 3:
                            # 港股: 确保4位数字 + .HK 
                            # 00700 -> 0700.HK (不能是700.HK)
                            # 01810 -> 1810.HK
                            clean_code = "{:04d}".format(int(code))
                            code = f"{clean_code}.HK"
                        
                        codes.add(code)
            return list(codes)
        except Exception as e:
            logger.error(f"获取自选股失败: {e}")
            return []

    async def _sync_single_stock(self, symbol: str) -> int:
        """同步单只股票新闻"""
        
        # 在线程池中运行yfinance (它是同步库)
        loop = asyncio.get_event_loop()
        news_list = await loop.run_in_executor(None, self._fetch_yfinance_raw, symbol)
        
        if not news_list:
            return 0

        # 标准化新闻格式
        normalized_news = []
        for n in news_list:
            # yfinance news 结构:
            # {
            #   "uuid": "...",
            #   "title": "...",
            #   "publisher": "...",
            #   "link": "...",
            #   "providerPublishTime": 167...
            #   "type": "STORY"
            # }
            
            # 过滤非STORY类型 (如VIDEO)
            if n.get("type") != "STORY":
                continue

            pub_time = datetime.fromtimestamp(n.get("providerPublishTime", 0), tz=timezone.utc)
            
            news_item = {
                "title": n.get("title"),
                "content": n.get("title"), # yfinance列表通常没有正文，用标题占位或不存content
                "summary": n.get("title"), # 同上
                "publish_time": pub_time,
                "url": n.get("link"),
                "source": f"yfinance:{n.get('publisher', 'unknown')}",
                "symbol": symbol,
                "data_source": "yfinance",
                "market": self._guess_market(symbol)
            }
            normalized_news.append(news_item)

        # 保存到数据库
        if normalized_news:
            return await self.news_service.save_news_data(
                news_data=normalized_news,
                data_source="yfinance",
                market="global" # 混合市场
            )
        return 0

    def _fetch_yfinance_raw(self, symbol: str) -> List[Dict]:
        """调用yfinance获取原始数据 (同步方法)"""
        try:
            ticker = yf.Ticker(symbol)
            return ticker.news
        except Exception as e:
            logger.warning(f"yfinance fetch error for {symbol}: {e}")
            return []

    def _guess_market(self, symbol: str) -> str:
        """简单的市场推断"""
        if symbol.endswith(".HK"): return "HK"
        if symbol.endswith(".SZ") or symbol.endswith(".SS"): return "CN"
        return "US"

# 全局实例
_yfinance_sync_service = None

async def get_yfinance_sync_service():
    global _yfinance_sync_service
    if _yfinance_sync_service is None:
        _yfinance_sync_service = YFinanceNewsSyncService()
        await _yfinance_sync_service.initialize()
    return _yfinance_sync_service

async def run_yfinance_news_sync():
    """Wrapper for scheduler"""
    try:
        service = await get_yfinance_sync_service()
        await service.sync_favorites_news()
    except Exception as e:
        logger.error(f"YFinance定时任务执行失败: {e}")
