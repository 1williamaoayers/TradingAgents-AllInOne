"""
FinnHub新闻源适配器 - 修复版
增加超时时间和更好的错误处理
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
import os
import aiohttp
import asyncio

from app.worker.news_adapters.base import NewsSourceAdapter, create_standard_news_item

logger = logging.getLogger(__name__)


class FinnHubAdapter(NewsSourceAdapter):
    """FinnHub新闻源适配器"""
    
    def __init__(self):
        super().__init__("finnhub")
        self.api_key = os.getenv("FINNHUB_API_KEY", "")
        self.base_url = "https://finnhub.io/api/v1"
        self.timeout = 60  # 增加到60秒
        self.max_retries = 2
    
    async def get_news(self, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取指定股票的新闻"""
        try:
            if not self.api_key:
                logger.warning(f"[FinnHub] API Key未配置")
                return []
            
            # 标准化股票代码（去除.HK等后缀）
            clean_symbol = symbol.replace('.HK', '').replace('.SH', '').replace('.SZ', '')
            
            # FinnHub主要支持美股，港股代码需要转换
            if clean_symbol.isdigit():
                logger.debug(f"[FinnHub] 跳过港股代码: {symbol}")
                return []

            # 调用FinnHub API
            url = f"{self.base_url}/company-news"
            params = {
                "symbol": clean_symbol,
                "from": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                "to": datetime.now().strftime("%Y-%m-%d"),
                "token": self.api_key
            }
            
            # 使用重试机制
            for attempt in range(self.max_retries):
                try:
                    timeout = aiohttp.ClientTimeout(total=self.timeout)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.get(url, params=params) as response:
                            if response.status == 200:
                                raw_news_list = await response.json()
                                break
                            elif response.status == 429:
                                logger.warning(f"[FinnHub] API限流，等待重试...")
                                await asyncio.sleep(5)
                                continue
                            else:
                                logger.warning(f"[FinnHub] API返回错误: {response.status}")
                                return []
                except asyncio.TimeoutError:
                    logger.warning(f"[FinnHub] 请求超时 (尝试 {attempt + 1}/{self.max_retries})")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2)
                    continue
            else:
                logger.error(f"[FinnHub] 所有重试都失败: {symbol}")
                return []
            
            if not raw_news_list:
                return []
            
            # 格式化为统一格式
            news_list = [
                self.normalize_news(raw_news, symbol)
                for raw_news in raw_news_list[:limit]
            ]
            
            logger.info(f"[FinnHub] {symbol} 获取到 {len(news_list)} 条新闻")
            return news_list
            
        except Exception as e:
            logger.error(f"[FinnHub] 获取新闻失败: {symbol} - {e}")
            return []  # 返回空列表而不是抛出异常

    def normalize_news(self, raw_news: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """格式化FinnHub新闻为统一格式"""
        # 解析发布时间
        publish_time = datetime.utcnow()
        if "datetime" in raw_news:
            try:
                publish_time = datetime.fromtimestamp(raw_news["datetime"])
            except:
                pass
        
        return create_standard_news_item(
            symbol=symbol,
            title=raw_news.get("headline", ""),
            source="FinnHub",
            summary=raw_news.get("summary", ""),
            content=raw_news.get("summary", ""),
            source_type="api",
            url=raw_news.get("url", ""),
            publish_time=publish_time,
            sentiment="neutral",
            relevance_score=0.8,
            tags=[]
        )
