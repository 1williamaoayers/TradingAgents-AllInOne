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
        """同步所有自选股的YFinance新闻"""
        logger.info("🔄 开始同步自选股YFinance新闻...")
        
        stats = {
            "total_processed": 0,
            "success_count": 0,
            "error_count": 0,
            "news_count": 0,
            "start_time": datetime.utcnow()
        }

        try:
            symbols = await self._get_favorite_stocks()
            if not symbols:
                logger.warning("⚠️ 没有找到自选股")
                return stats
            
            stats["total_processed"] = len(symbols)
            logger.info(f"📊 需处理自选股: {len(symbols)} 只")

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
        """获取去重后的自选股代码，正确转换为yfinance格式"""
        try:
            favorites_docs = await self.db.user_favorites.find(
                {}, {"favorites": 1, "_id": 0}
            ).to_list(None)
            
            codes = set()
            for doc in favorites_docs:
                for fav in doc.get("favorites", []):
                    code = fav.get("stock_code")
                    market = fav.get("market", "")
                    
                    if not code:
                        continue
                    
                    # 根据market字段正确转换代码
                    if market == "港股":
                        # 港股: 01810 -> 1810.HK
                        if code.isdigit():
                            clean_code = "{:04d}".format(int(code))
                            code = f"{clean_code}.HK"
                        elif not code.endswith(".HK"):
                            code = f"{code}.HK"
                    elif market == "A股":
                        # A股: 000001 -> 000001.SZ 或 600519 -> 600519.SS
                        if code.isdigit():
                            if code.startswith("6"):
                                code = f"{code}.SS"  # 上海
                            else:
                                code = f"{code}.SZ"  # 深圳
                    elif market == "美股":
                        # 美股: 保持原样 (TSLA, GOOGL)
                        pass
                    else:
                        # 未知市场，尝试智能判断
                        if code.isdigit() and len(code) >= 4:
                            clean_code = "{:04d}".format(int(code))
                            code = f"{clean_code}.HK"
                    
                    codes.add(code)
                    logger.debug(f"转换股票代码: {fav.get('stock_code')} ({market}) -> {code}")
            
            return list(codes)
        except Exception as e:
            logger.error(f"获取自选股失败: {e}")
            return []

    async def _sync_single_stock(self, symbol: str) -> int:
        """同步单只股票新闻"""
        loop = asyncio.get_event_loop()
        news_list = await loop.run_in_executor(None, self._fetch_yfinance_raw, symbol)
        
        if not news_list:
            return 0

        normalized_news = []
        for n in news_list:
            # yfinance 1.1.0+ 新结构: content 嵌套
            content = n.get("content", n)  # 兼容新旧结构
            
            # 过滤非 STORY 类型
            content_type = content.get("contentType") or n.get("type")
            if content_type != "STORY":
                continue
            
            # 解析发布时间 (新结构用 pubDate ISO格式，旧结构用 providerPublishTime 时间戳)
            pub_date_str = content.get("pubDate")
            if pub_date_str:
                try:
                    pub_time = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
                except:
                    pub_time = datetime.now(timezone.utc)
            else:
                ts = n.get("providerPublishTime", 0)
                pub_time = datetime.fromtimestamp(ts, tz=timezone.utc) if ts else datetime.now(timezone.utc)
            
            # 获取标题和摘要
            title = content.get("title") or n.get("title", "")
            summary = content.get("summary") or content.get("description") or title
            
            # 获取 URL
            canonical = content.get("canonicalUrl", {})
            url = canonical.get("url") if isinstance(canonical, dict) else n.get("link", "")
            
            # 获取来源
            provider = content.get("provider", {})
            source_name = provider.get("displayName") if isinstance(provider, dict) else n.get("publisher", "Yahoo")
            
            news_item = {
                "title": title,
                "content": summary,
                "summary": summary,
                "publish_time": pub_time,
                "url": url,
                "source": f"yfinance:{source_name}",
                "symbol": symbol,
                "data_source": "yfinance",
                "market": self._guess_market(symbol)
            }
            normalized_news.append(news_item)

        if normalized_news:
            return await self.news_service.save_news_data(
                news_data=normalized_news,
                data_source="yfinance",
                market="global"
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
