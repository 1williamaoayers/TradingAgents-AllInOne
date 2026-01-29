"""
RSS新闻源适配器
从数据库读取RSS订阅源，获取中文财经新闻并智能过滤相关内容
"""
import logging
from typing import List, Dict, Any
from datetime import datetime
import feedparser

from app.worker.news_adapters.base import NewsSourceAdapter, create_standard_news_item
from app.core.database import get_mongo_db

logger = logging.getLogger(__name__)


class RSSAdapter(NewsSourceAdapter):
    """RSS新闻源适配器 - 从数据库读取订阅源"""
    
    def __init__(self):
        super().__init__("rss")
        self.db = None
        # 备用硬编码源（数据库为空时使用）
        self.fallback_feeds = [
            "http://rsshub:1200/jin10",
            "http://rsshub:1200/cls/telegraph",
            "http://rsshub:1200/gelonghui/live",
            "http://rsshub:1200/wallstreetcn/news/global",
        ]
        
        # 股票代码到公司名的映射（用于过滤）
        self.stock_names = {
            "09618": ["京东", "JD", "jd.com"],
            "00700": ["腾讯", "Tencent", "微信", "WeChat"],
            "09988": ["阿里", "阿里巴巴", "Alibaba", "淘宝", "天猫"],
            "01810": ["小米", "Xiaomi", "米家"],
            "02128": ["联塑", "中国联塑"],
            "02525": ["禾赛", "Hesai", "激光雷达"],
            "01024": ["快手", "Kuaishou"],
            "09999": ["网易", "NetEase"],
            "03690": ["美团", "Meituan"],
            "09888": ["百度", "Baidu"],
            "TSLA": ["特斯拉", "Tesla", "马斯克", "Musk"],
            "GOOGL": ["谷歌", "Google", "Alphabet"],
        }
        
        # 通用港股市场关键词（宽松匹配）
        self.market_keywords = [
            "港股", "恒生", "恒指", "港交所", "南向资金", "北向资金",
            "科技股", "消费股", "金融股", "地产股", "新能源",
            "中概股", "回港", "二次上市", "IPO", "回购",
            "互联网", "电商", "智能驾驶", "AI", "人工智能",
            "美股", "纳斯达克", "标普", "道琼斯",
        ]
    
    def _get_db(self):
        """获取数据库连接"""
        if self.db is None:
            self.db = get_mongo_db()
        return self.db
    
    async def _load_feeds_from_db(self) -> List[str]:
        """从数据库加载活跃的RSS订阅源"""
        try:
            db = self._get_db()
            cursor = db.rss_subscriptions.find(
                {"is_active": True},
                {"url": 1, "name": 1, "_id": 0}
            )
            subscriptions = await cursor.to_list(None)
            
            if subscriptions:
                feeds = [sub["url"] for sub in subscriptions if sub.get("url")]
                logger.info(f"[RSS] 从数据库加载 {len(feeds)} 个订阅源")
                return feeds
            else:
                logger.warning("[RSS] 数据库无订阅源，使用备用源")
                return self.fallback_feeds
        except Exception as e:
            logger.error(f"[RSS] 加载订阅源失败: {e}，使用备用源")
            return self.fallback_feeds

    async def get_news(self, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取RSS新闻并智能过滤
        
        Args:
            symbol: 股票代码（空字符串表示获取所有市场新闻）
            limit: 最大新闻数量
            
        Returns:
            与股票相关的新闻列表
        """
        try:
            matched_news = []
            
            # 获取该股票的关键词
            clean_symbol = symbol.replace('.HK', '').replace('.SH', '').replace('.SZ', '')
            stock_keywords = self.stock_names.get(clean_symbol, [])
            
            # 从数据库加载RSS源
            rss_feeds = await self._load_feeds_from_db()
            
            # 获取所有RSS源的新闻
            for feed_url in rss_feeds:
                try:
                    feed = feedparser.parse(feed_url)
                    feed_name = feed.feed.get("title", feed_url)[:30]
                    
                    for entry in feed.entries[:50]:  # 每个源最多50条
                        title = entry.get("title", "")
                        summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
                        content = title + " " + summary
                        
                        # 智能过滤：检查是否与股票相关
                        is_related, match_type = self._check_relevance(
                            content, clean_symbol, stock_keywords
                        )
                        
                        if is_related:
                            news_item = self.normalize_news(entry, symbol)
                            news_item["match_type"] = match_type
                            news_item["feed_source"] = feed_name
                            matched_news.append(news_item)
                            
                            if len(matched_news) >= limit:
                                break
                    
                    if len(matched_news) >= limit:
                        break
                        
                except Exception as e:
                    logger.debug(f"[RSS] 解析RSS源失败 {feed_url}: {e}")
                    continue
            
            # 限制总数
            matched_news = matched_news[:limit]
            
            if matched_news:
                logger.info(f"[RSS] {symbol or '全市场'}: 获取到 {len(matched_news)} 条相关新闻")
            
            return matched_news
            
        except Exception as e:
            logger.error(f"[RSS] 获取新闻失败: {e}")
            return []

    def _check_relevance(self, content: str, symbol: str, stock_keywords: List[str]) -> tuple:
        """
        检查新闻是否与股票相关（宽松匹配）
        
        Args:
            content: 新闻内容（标题+摘要）
            symbol: 股票代码（不含.HK）
            stock_keywords: 该股票的关键词列表
            
        Returns:
            (是否相关, 匹配类型)
        """
        # 如果没有指定股票，返回所有市场相关新闻
        if not symbol:
            for keyword in self.market_keywords:
                if keyword in content:
                    return True, "market_keyword"
            # 宽松模式：财经类RSS源的新闻默认相关
            return True, "general_news"
        
        content_lower = content.lower()
        
        # 1. 精确匹配股票代码
        if symbol in content or f"{symbol}.HK" in content:
            return True, "stock_code"
        
        # 2. 匹配公司名称/关键词
        for keyword in stock_keywords:
            if keyword.lower() in content_lower:
                return True, "company_name"
        
        # 3. 宽松匹配：港股市场通用关键词
        for keyword in self.market_keywords:
            if keyword in content:
                return True, "market_keyword"
        
        return False, None

    def normalize_news(self, raw_news: Any, symbol: str) -> Dict[str, Any]:
        """
        格式化RSS新闻为统一格式
        
        Args:
            raw_news: RSS原始新闻
            symbol: 股票代码
            
        Returns:
            标准化的新闻字典
        """
        # 解析发布时间
        publish_time = datetime.utcnow()
        if hasattr(raw_news, "published_parsed"):
            try:
                from time import mktime
                publish_time = datetime.fromtimestamp(mktime(raw_news.published_parsed))
            except:
                pass
        
        # 获取内容
        summary = ""
        if hasattr(raw_news, "summary"):
            summary = raw_news.summary
        elif hasattr(raw_news, "description"):
            summary = raw_news.description
        
        return create_standard_news_item(
            symbol=symbol or "MARKET",
            title=raw_news.get("title", ""),
            source="RSS",
            summary=summary[:500] if summary else "",
            content=summary,
            source_type="rss",
            url=raw_news.get("link", ""),
            publish_time=publish_time,
            sentiment="neutral",
            relevance_score=0.7,
            tags=[]
        )
