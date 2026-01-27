#!/usr/bin/env python3
"""
港股沽空数据模块
从港交所/东方财富获取每日沽空数据，支持历史数据积累和查询

数据源优先级：
1. 东方财富 API（主要数据源，数据完整）
2. 港交所官网（备用数据源）
"""

import os
import time
import json
import re
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set, Callable

import requests
from bs4 import BeautifulSoup

# 导入统一日志系统
try:
    from tradingagents.utils.logging_init import get_logger
    logger = get_logger("default")
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# 导入运行时配置
try:
    from tradingagents.config.runtime_settings import get_int, get_float
except ImportError:
    def get_int(env_key, config_key, default):
        return int(os.environ.get(env_key, default))
    def get_float(env_key, config_key, default):
        return float(os.environ.get(env_key, default))


# ============================================================================
# 数据模型
# ============================================================================

@dataclass
class ShortSellingRecord:
    """沽空记录数据模型"""
    
    stock_code: str          # 股票代码（5位格式，如 "00700"）
    stock_name: str          # 股票名称
    date: str                # 日期（YYYY-MM-DD 格式）
    short_shares: int        # 沽空股数
    short_value: float       # 沽空金额（港元）
    short_ratio: float       # 沽空比例（小数，如 0.0523 表示 5.23%）
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "date": self.date,
            "short_shares": self.short_shares,
            "short_value": self.short_value,
            "short_ratio": self.short_ratio,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ShortSellingRecord":
        """从字典创建实例"""
        created_at = data.get("created_at")
        updated_at = data.get("updated_at")
        
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()
            
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        elif updated_at is None:
            updated_at = datetime.now()
        
        return cls(
            stock_code=data["stock_code"],
            stock_name=data["stock_name"],
            date=data["date"],
            short_shares=int(data["short_shares"]),
            short_value=float(data["short_value"]),
            short_ratio=float(data["short_ratio"]),
            created_at=created_at,
            updated_at=updated_at
        )


# ============================================================================
# HTML 解析器
# ============================================================================

class HKEXShortSellingParser:
    """港交所沽空报告 HTML 解析器"""
    
    def parse(self, html_content: str, date: str) -> List[ShortSellingRecord]:
        """
        解析 HTML 内容提取沽空记录
        
        Args:
            html_content: HTML 字符串
            date: 数据日期 (YYYY-MM-DD)
            
        Returns:
            解析后的沽空记录列表
        """
        records = []
        now = datetime.now()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 查找数据表格
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    
                    # 跳过表头行
                    if len(cells) < 5:
                        continue
                    
                    # 检查是否是数据行（第一列应该是股票代码）
                    first_cell = cells[0].get_text(strip=True)
                    if not first_cell or not first_cell.replace('.', '').isdigit():
                        continue
                    
                    try:
                        # 解析各字段
                        stock_code = self._normalize_stock_code(first_cell)
                        stock_name = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                        
                        # 沽空股数（第3列）
                        short_shares_str = cells[2].get_text(strip=True) if len(cells) > 2 else "0"
                        short_shares = self._parse_numeric(short_shares_str)
                        
                        # 沽空金额（第4列）
                        short_value_str = cells[3].get_text(strip=True) if len(cells) > 3 else "0"
                        short_value = self._parse_numeric(short_value_str)
                        
                        # 沽空比例（第5列）
                        short_ratio_str = cells[4].get_text(strip=True) if len(cells) > 4 else "0%"
                        short_ratio = self._parse_ratio(short_ratio_str)
                        
                        if short_shares is None or short_value is None or short_ratio is None:
                            logger.warning(f"⚠️ [沽空解析] 跳过无效记录: {stock_code}")
                            continue
                        
                        record = ShortSellingRecord(
                            stock_code=stock_code,
                            stock_name=stock_name,
                            date=date,
                            short_shares=int(short_shares),
                            short_value=float(short_value),
                            short_ratio=float(short_ratio),
                            created_at=now,
                            updated_at=now
                        )
                        records.append(record)
                        
                    except Exception as e:
                        logger.warning(f"⚠️ [沽空解析] 解析行失败: {e}")
                        continue
            
            logger.info(f"✅ [沽空解析] 成功解析 {len(records)} 条记录")
            
        except Exception as e:
            logger.error(f"❌ [沽空解析] HTML 解析失败: {e}")
        
        return records
    
    def _normalize_stock_code(self, code: str) -> str:
        """
        标准化股票代码为 5 位格式
        
        Args:
            code: 原始股票代码
            
        Returns:
            5 位格式的股票代码
        """
        # 移除非数字字符
        clean_code = re.sub(r'[^\d]', '', code)
        
        # 补齐到 5 位
        return clean_code.zfill(5)
    
    def _parse_numeric(self, value: str) -> Optional[float]:
        """
        解析数值字符串，处理逗号分隔符
        
        Args:
            value: 数值字符串（如 "1,234,567"）
            
        Returns:
            解析后的数值，失败返回 None
        """
        if not value:
            return None
        
        try:
            # 移除逗号和空格
            clean_value = value.replace(',', '').replace(' ', '').strip()
            
            # 处理空字符串
            if not clean_value or clean_value == '-':
                return 0.0
            
            return float(clean_value)
        except (ValueError, TypeError):
            return None
    
    def _parse_ratio(self, value: str) -> Optional[float]:
        """
        解析百分比字符串为小数
        
        Args:
            value: 百分比字符串（如 "5.23%"）
            
        Returns:
            小数值（如 0.0523），失败返回 None
        """
        if not value:
            return None
        
        try:
            # 移除百分号和空格
            clean_value = value.replace('%', '').replace(' ', '').strip()
            
            # 处理空字符串
            if not clean_value or clean_value == '-':
                return 0.0
            
            # 转换为小数
            return float(clean_value) / 100.0
        except (ValueError, TypeError):
            return None


# ============================================================================
# 速率限制器
# ============================================================================

class RateLimiter:
    """速率限制器"""
    
    def __init__(self, min_interval: float = None):
        """
        初始化速率限制器
        
        Args:
            min_interval: 最小请求间隔（秒），默认从环境变量读取
        """
        if min_interval is None:
            min_interval = get_float(
                "TA_HK_SHORT_RATE_LIMIT_SECONDS",
                "ta_hk_short_rate_limit_seconds",
                5.0
            )
        
        self.min_interval = min_interval
        self.last_request_time = 0.0
        self._lock = threading.Lock()
    
    def acquire(self) -> None:
        """获取请求许可，必要时等待"""
        with self._lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_interval:
                wait_time = self.min_interval - time_since_last
                logger.debug(f"⏱️ [速率限制] 等待 {wait_time:.2f} 秒")
                time.sleep(wait_time)
            
            self.last_request_time = time.time()
    
    def reset(self) -> None:
        """重置限制器状态"""
        with self._lock:
            self.last_request_time = 0.0


# ============================================================================
# MongoDB 存储层
# ============================================================================

class ShortSellingRepository:
    """沽空数据 MongoDB 存储层"""
    
    COLLECTION_NAME = "hk_short_selling"
    
    def __init__(self, db_client=None):
        """
        初始化存储层
        
        Args:
            db_client: MongoDB 客户端，如果为 None 则尝试自动获取
        """
        self.db_client = db_client
        self.collection = None
        
        if db_client is not None:
            self._init_collection()
    
    def _init_collection(self):
        """初始化集合并创建索引"""
        if self.db_client is None:
            return
        
        try:
            # 获取数据库
            db = self.db_client.get_database()
            self.collection = db[self.COLLECTION_NAME]
            
            # 创建索引
            self.collection.create_index(
                [("stock_code", 1), ("date", 1)],
                unique=True,
                name="idx_stock_date"
            )
            self.collection.create_index([("date", 1)], name="idx_date")
            self.collection.create_index([("short_ratio", -1)], name="idx_ratio")
            
            logger.info(f"✅ [MongoDB] 初始化集合 {self.COLLECTION_NAME} 完成")
            
        except Exception as e:
            logger.error(f"❌ [MongoDB] 初始化集合失败: {e}")
    
    def set_client(self, db_client):
        """设置 MongoDB 客户端"""
        self.db_client = db_client
        self._init_collection()
    
    def upsert_records(self, records: List[ShortSellingRecord]) -> int:
        """
        批量插入或更新记录
        
        Args:
            records: 沽空记录列表
            
        Returns:
            受影响的记录数
        """
        if not self.collection or not records:
            return 0
        
        affected = 0
        now = datetime.now()
        
        try:
            from pymongo import UpdateOne
            
            operations = []
            for record in records:
                doc = record.to_dict()
                doc["updated_at"] = now.isoformat()
                
                operations.append(
                    UpdateOne(
                        {"stock_code": record.stock_code, "date": record.date},
                        {"$set": doc, "$setOnInsert": {"created_at": now.isoformat()}},
                        upsert=True
                    )
                )
            
            if operations:
                result = self.collection.bulk_write(operations)
                affected = result.upserted_count + result.modified_count
                logger.info(f"✅ [MongoDB] 批量更新 {affected} 条记录")
            
        except Exception as e:
            logger.error(f"❌ [MongoDB] 批量更新失败: {e}")
        
        return affected
    
    def find_by_stock_and_date(self, stock_code: str, date: str) -> Optional[Dict]:
        """按股票代码和日期查询"""
        if not self.collection:
            return None
        
        try:
            # 标准化股票代码
            normalized_code = stock_code.zfill(5)
            
            doc = self.collection.find_one({
                "stock_code": normalized_code,
                "date": date
            })
            
            if doc:
                doc.pop("_id", None)
                return doc
            
        except Exception as e:
            logger.error(f"❌ [MongoDB] 查询失败: {e}")
        
        return None
    
    def find_by_stock_and_date_range(
        self, 
        stock_code: str, 
        start_date: str, 
        end_date: str
    ) -> List[Dict]:
        """按股票代码和日期范围查询"""
        if not self.collection:
            return []
        
        try:
            normalized_code = stock_code.zfill(5)
            
            cursor = self.collection.find({
                "stock_code": normalized_code,
                "date": {"$gte": start_date, "$lte": end_date}
            }).sort("date", 1)
            
            results = []
            for doc in cursor:
                doc.pop("_id", None)
                results.append(doc)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ [MongoDB] 范围查询失败: {e}")
        
        return []
    
    def find_top_by_ratio(self, date: str, limit: int = 20) -> List[Dict]:
        """按沽空比例降序查询前 N 条"""
        if not self.collection:
            return []
        
        try:
            cursor = self.collection.find({
                "date": date
            }).sort("short_ratio", -1).limit(limit)
            
            results = []
            for doc in cursor:
                doc.pop("_id", None)
                results.append(doc)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ [MongoDB] Top N 查询失败: {e}")
        
        return []
    
    def get_dates_with_data(self, start_date: str, end_date: str) -> Set[str]:
        """获取指定范围内已有数据的日期集合"""
        if not self.collection:
            return set()
        
        try:
            cursor = self.collection.distinct("date", {
                "date": {"$gte": start_date, "$lte": end_date}
            })
            
            return set(cursor)
            
        except Exception as e:
            logger.error(f"❌ [MongoDB] 获取日期集合失败: {e}")
        
        return set()
    
    def get_market_stats(self, date: str) -> Optional[Dict]:
        """获取指定日期的市场统计"""
        if not self.collection:
            return None
        
        try:
            pipeline = [
                {"$match": {"date": date}},
                {"$group": {
                    "_id": None,
                    "total_short_shares": {"$sum": "$short_shares"},
                    "total_short_value": {"$sum": "$short_value"},
                    "avg_short_ratio": {"$avg": "$short_ratio"},
                    "max_short_ratio": {"$max": "$short_ratio"},
                    "stock_count": {"$sum": 1}
                }}
            ]
            
            result = list(self.collection.aggregate(pipeline))
            
            if result:
                stats = result[0]
                stats.pop("_id", None)
                stats["date"] = date
                return stats
            
        except Exception as e:
            logger.error(f"❌ [MongoDB] 市场统计查询失败: {e}")
        
        return None


# ============================================================================
# Redis 缓存层
# ============================================================================

class ShortSellingCache:
    """沽空数据 Redis 缓存层"""
    
    KEY_PREFIX = "hk_short"
    DEFAULT_TTL = 86400  # 24 小时
    
    def __init__(self, redis_client=None):
        """
        初始化缓存层
        
        Args:
            redis_client: Redis 客户端
        """
        self.redis_client = redis_client
    
    def set_client(self, redis_client):
        """设置 Redis 客户端"""
        self.redis_client = redis_client
    
    def _make_key(self, *parts) -> str:
        """生成缓存键"""
        return ":".join([self.KEY_PREFIX] + list(parts))
    
    def get_stock_data(self, stock_code: str, date: str) -> Optional[Dict]:
        """获取缓存的股票沽空数据"""
        if not self.redis_client:
            return None
        
        try:
            normalized_code = stock_code.zfill(5)
            key = self._make_key(normalized_code, date)
            
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            
        except Exception as e:
            logger.warning(f"⚠️ [Redis] 读取缓存失败: {e}")
        
        return None
    
    def set_stock_data(
        self, 
        stock_code: str, 
        date: str, 
        data: Dict,
        ttl: int = None
    ) -> None:
        """缓存股票沽空数据"""
        if not self.redis_client:
            return
        
        try:
            normalized_code = stock_code.zfill(5)
            key = self._make_key(normalized_code, date)
            
            self.redis_client.setex(
                key,
                ttl or self.DEFAULT_TTL,
                json.dumps(data, ensure_ascii=False)
            )
            
        except Exception as e:
            logger.warning(f"⚠️ [Redis] 写入缓存失败: {e}")
    
    def get_daily_stats(self, date: str) -> Optional[Dict]:
        """获取缓存的每日统计"""
        if not self.redis_client:
            return None
        
        try:
            key = self._make_key("daily", date)
            
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            
        except Exception as e:
            logger.warning(f"⚠️ [Redis] 读取每日统计缓存失败: {e}")
        
        return None
    
    def set_daily_stats(self, date: str, stats: Dict, ttl: int = None) -> None:
        """缓存每日统计"""
        if not self.redis_client:
            return
        
        try:
            key = self._make_key("daily", date)
            
            self.redis_client.setex(
                key,
                ttl or self.DEFAULT_TTL,
                json.dumps(stats, ensure_ascii=False)
            )
            
        except Exception as e:
            logger.warning(f"⚠️ [Redis] 写入每日统计缓存失败: {e}")
    
    def get_top_stocks(self, date: str, top_n: int) -> Optional[List[Dict]]:
        """获取缓存的 Top N 股票"""
        if not self.redis_client:
            return None
        
        try:
            key = self._make_key("top", date, str(top_n))
            
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            
        except Exception as e:
            logger.warning(f"⚠️ [Redis] 读取 Top N 缓存失败: {e}")
        
        return None
    
    def set_top_stocks(self, date: str, top_n: int, stocks: List[Dict], ttl: int = None) -> None:
        """缓存 Top N 股票"""
        if not self.redis_client:
            return
        
        try:
            key = self._make_key("top", date, str(top_n))
            
            self.redis_client.setex(
                key,
                ttl or self.DEFAULT_TTL,
                json.dumps(stocks, ensure_ascii=False)
            )
            
        except Exception as e:
            logger.warning(f"⚠️ [Redis] 写入 Top N 缓存失败: {e}")
    
    def invalidate_date(self, date: str) -> int:
        """使指定日期的所有缓存失效"""
        if not self.redis_client:
            return 0
        
        try:
            pattern = self._make_key("*", date) + "*"
            keys = list(self.redis_client.scan_iter(match=pattern))
            
            if keys:
                return self.redis_client.delete(*keys)
            
        except Exception as e:
            logger.warning(f"⚠️ [Redis] 清除缓存失败: {e}")
        
        return 0


# ============================================================================
# 核心数据提供器
# ============================================================================

class HKShortSellingProvider:
    """港股沽空数据提供器"""
    
    # 港交所沽空数据 URL 模板
    HKEX_URL_TEMPLATE = "https://www.hkex.com.hk/chi/stat/smstat/ssturnover/ncms/ASHTMAIN_{date}.htm"
    
    # 备用 URL 模板
    HKEX_URL_TEMPLATE_ALT = "https://www.hkex.com.hk/eng/stat/smstat/ssturnover/ncms/ASHTMAIN_{date}.htm"
    
    # 东方财富 API（主要数据源）
    EASTMONEY_API = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    
    def __init__(
        self,
        mongodb_client=None,
        redis_client=None,
        rate_limiter: RateLimiter = None
    ):
        """
        初始化提供器
        
        Args:
            mongodb_client: MongoDB 客户端
            redis_client: Redis 客户端
            rate_limiter: 速率限制器
        """
        self.parser = HKEXShortSellingParser()
        self.repository = ShortSellingRepository(mongodb_client)
        self.cache = ShortSellingCache(redis_client)
        self.rate_limiter = rate_limiter or RateLimiter()
        
        # HTTP 请求配置
        self.timeout = get_int("TA_HK_SHORT_TIMEOUT", "ta_hk_short_timeout", 30)
        self.max_retries = get_int("TA_HK_SHORT_MAX_RETRIES", "ta_hk_short_max_retries", 3)
        
        # 请求头
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }
    
    def set_mongodb_client(self, client):
        """设置 MongoDB 客户端"""
        self.repository.set_client(client)
    
    def set_redis_client(self, client):
        """设置 Redis 客户端"""
        self.cache.set_client(client)
    
    def _fetch_from_eastmoney(self, date: str = None, stock_code: str = None, page_size: int = 500) -> List[ShortSellingRecord]:
        """
        从东方财富 API 获取沽空数据
        
        Args:
            date: 日期 (YYYY-MM-DD)，为 None 时获取最新数据
            stock_code: 股票代码，为 None 时获取所有股票
            page_size: 每页数量
            
        Returns:
            沽空记录列表
        """
        records = []
        now = datetime.now()
        
        try:
            # 构建请求参数
            params = {
                "sortColumns": "TRADE_DATE,SHORT_SELLING_RATIO",
                "sortTypes": "-1,-1",
                "pageSize": page_size,
                "pageNumber": 1,
                "reportName": "RPT_HK_SHORTSELLING",
                "columns": "ALL"
            }
            
            # 添加过滤条件
            filters = []
            if date:
                # 格式化日期为东方财富格式
                filters.append(f'(TRADE_DATE=\'{date}\')')
            if stock_code:
                normalized_code = stock_code.zfill(5)
                filters.append(f'(SECURITY_CODE="{normalized_code}")')
            
            if filters:
                params["filter"] = "".join(filters)
            
            # 速率限制
            self.rate_limiter.acquire()
            
            logger.info(f"🔄 [东方财富] 获取沽空数据: date={date}, stock={stock_code}")
            
            response = requests.get(
                self.EASTMONEY_API,
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                logger.warning(f"⚠️ [东方财富] HTTP {response.status_code}")
                return records
            
            data = response.json()
            
            if not data.get("success") or not data.get("result"):
                logger.warning(f"⚠️ [东方财富] API 返回失败: {data.get('message')}")
                return records
            
            result_data = data["result"].get("data", [])
            
            for item in result_data:
                try:
                    # 解析日期
                    trade_date = item.get("TRADE_DATE", "")
                    if trade_date:
                        trade_date = trade_date.split(" ")[0]  # 去掉时间部分
                    
                    # 沽空比例（东方财富返回的是百分比，需要转换为小数）
                    short_ratio = item.get("SHORT_SELLING_RATIO", 0)
                    if short_ratio:
                        short_ratio = float(short_ratio) / 100.0
                    
                    record = ShortSellingRecord(
                        stock_code=item.get("SECURITY_CODE", "").zfill(5),
                        stock_name=item.get("SECURITY_NAME_ABBR", ""),
                        date=trade_date,
                        short_shares=int(item.get("SHORT_SELLING_SHARES", 0) or 0),
                        short_value=float(item.get("SHORT_SELLING_AMT", 0) or 0),
                        short_ratio=short_ratio,
                        created_at=now,
                        updated_at=now
                    )
                    records.append(record)
                    
                except Exception as e:
                    logger.warning(f"⚠️ [东方财富] 解析记录失败: {e}")
                    continue
            
            logger.info(f"✅ [东方财富] 获取到 {len(records)} 条记录")
            
        except Exception as e:
            logger.error(f"❌ [东方财富] 获取失败: {e}")
        
        return records
    
    def _format_date_for_url(self, date: str) -> str:
        """将日期格式化为 URL 所需格式 (YYYYMMDD)"""
        return date.replace("-", "")
    
    def _fetch_html(self, date: str) -> Optional[str]:
        """
        从港交所获取 HTML 内容
        
        Args:
            date: 日期 (YYYY-MM-DD)
            
        Returns:
            HTML 内容，失败返回 None
        """
        url_date = self._format_date_for_url(date)
        urls = [
            self.HKEX_URL_TEMPLATE.format(date=url_date),
            self.HKEX_URL_TEMPLATE_ALT.format(date=url_date)
        ]
        
        for url in urls:
            for attempt in range(self.max_retries):
                try:
                    # 速率限制
                    self.rate_limiter.acquire()
                    
                    logger.info(f"🔄 [沽空数据] 请求: {url} (尝试 {attempt + 1}/{self.max_retries})")
                    
                    response = requests.get(
                        url,
                        headers=self.headers,
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"✅ [沽空数据] 获取成功: {date}")
                        return response.text
                    
                    elif response.status_code == 404:
                        logger.warning(f"⚠️ [沽空数据] 数据不存在: {date}")
                        break  # 尝试下一个 URL
                    
                    else:
                        logger.warning(f"⚠️ [沽空数据] HTTP {response.status_code}: {url}")
                        
                except requests.exceptions.Timeout:
                    logger.warning(f"⚠️ [沽空数据] 请求超时: {url}")
                    
                except requests.exceptions.RequestException as e:
                    logger.warning(f"⚠️ [沽空数据] 请求失败: {e}")
                
                # 指数退避
                if attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt) * 2
                    logger.debug(f"⏱️ [沽空数据] 等待 {wait_time} 秒后重试")
                    time.sleep(wait_time)
        
        logger.error(f"❌ [沽空数据] 所有尝试均失败: {date}")
        return None
    
    def fetch_daily_data(self, date: str) -> List[ShortSellingRecord]:
        """
        获取指定日期的沽空数据
        
        数据源优先级：
        1. 东方财富 API（主要数据源）
        2. 港交所官网（备用数据源）
        
        Args:
            date: 日期 (YYYY-MM-DD)
            
        Returns:
            沽空记录列表
        """
        records = []
        
        # 优先使用东方财富 API
        logger.info(f"📊 [沽空数据] 获取 {date} 的数据...")
        records = self._fetch_from_eastmoney(date=date)
        
        # 如果东方财富失败，尝试港交所
        if not records:
            logger.info(f"🔄 [沽空数据] 东方财富无数据，尝试港交所...")
            html_content = self._fetch_html(date)
            if html_content:
                records = self.parser.parse(html_content, date)
        
        if records:
            # 存储到 MongoDB
            self.repository.upsert_records(records)
            
            # 清除相关缓存
            self.cache.invalidate_date(date)
            
            logger.info(f"✅ [沽空数据] {date}: 获取并存储 {len(records)} 条记录")
        else:
            logger.warning(f"⚠️ [沽空数据] {date}: 未获取到数据")
        
        return records
    
    def get_stock_short_data(self, stock_code: str, date: str) -> Optional[Dict]:
        """
        获取特定股票在特定日期的沽空数据
        
        Args:
            stock_code: 股票代码
            date: 日期
            
        Returns:
            沽空数据字典或 None
        """
        normalized_code = stock_code.zfill(5)
        
        # 先查缓存
        cached = self.cache.get_stock_data(normalized_code, date)
        if cached:
            logger.debug(f"⚡ [沽空数据] 缓存命中: {normalized_code} @ {date}")
            return cached
        
        # 查数据库
        data = self.repository.find_by_stock_and_date(normalized_code, date)
        
        if data:
            # 写入缓存
            self.cache.set_stock_data(normalized_code, date, data)
        
        return data
    
    def get_stock_short_history(
        self, 
        stock_code: str, 
        start_date: str, 
        end_date: str
    ) -> List[Dict]:
        """
        获取股票的沽空历史数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            沽空记录列表
        """
        return self.repository.find_by_stock_and_date_range(
            stock_code, start_date, end_date
        )
    
    def get_top_short_stocks(self, date: str, top_n: int = 20) -> List[Dict]:
        """
        获取指定日期沽空比例最高的股票
        
        Args:
            date: 日期
            top_n: 返回数量
            
        Returns:
            按沽空比例降序排列的股票列表
        """
        # 先查缓存
        cached = self.cache.get_top_stocks(date, top_n)
        if cached:
            return cached
        
        # 查数据库
        stocks = self.repository.find_top_by_ratio(date, top_n)
        
        if stocks:
            # 写入缓存
            self.cache.set_top_stocks(date, top_n, stocks)
        
        return stocks
    
    def get_market_short_stats(self, date: str) -> Optional[Dict]:
        """
        获取全市场沽空统计
        
        Args:
            date: 日期
            
        Returns:
            市场统计数据
        """
        # 先查缓存
        cached = self.cache.get_daily_stats(date)
        if cached:
            return cached
        
        # 查数据库
        stats = self.repository.get_market_stats(date)
        
        if stats:
            # 写入缓存
            self.cache.set_daily_stats(date, stats)
        
        return stats
    
    def backfill_history(
        self, 
        start_date: str, 
        end_date: str, 
        force: bool = False,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> Dict:
        """
        回填历史数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            force: 是否强制刷新已有数据
            progress_callback: 进度回调函数 (date, current, total)
            
        Returns:
            回填结果统计
        """
        result = {
            "success": True,
            "start_date": start_date,
            "end_date": end_date,
            "total_dates": 0,
            "processed_dates": 0,
            "skipped_dates": 0,
            "failed_dates": [],
            "total_records": 0
        }
        
        # 生成日期列表
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        dates = []
        current = start
        while current <= end:
            # 跳过周末
            if current.weekday() < 5:
                dates.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)
        
        result["total_dates"] = len(dates)
        
        # 获取已有数据的日期
        existing_dates = set()
        if not force:
            existing_dates = self.repository.get_dates_with_data(start_date, end_date)
        
        # 逐日处理
        for i, date in enumerate(dates):
            if progress_callback:
                progress_callback(date, i + 1, len(dates))
            
            # 跳过已有数据
            if date in existing_dates:
                logger.info(f"⏭️ [回填] 跳过已有数据: {date}")
                result["skipped_dates"] += 1
                continue
            
            try:
                records = self.fetch_daily_data(date)
                result["processed_dates"] += 1
                result["total_records"] += len(records)
                
                logger.info(f"✅ [回填] {date}: {len(records)} 条记录")
                
            except Exception as e:
                logger.error(f"❌ [回填] {date} 失败: {e}")
                result["failed_dates"].append(date)
        
        if result["failed_dates"]:
            result["success"] = False
        
        return result


# ============================================================================
# 定时调度器
# ============================================================================

class ShortSellingScheduler:
    """沽空数据采集定时调度器"""
    
    # 香港公众假期（需要定期更新）
    HK_HOLIDAYS_2024 = {
        "2024-01-01", "2024-02-10", "2024-02-11", "2024-02-12", "2024-02-13",
        "2024-03-29", "2024-04-01", "2024-04-04", "2024-05-01", "2024-05-15",
        "2024-06-10", "2024-07-01", "2024-09-18", "2024-10-01", "2024-10-11",
        "2024-12-25", "2024-12-26"
    }
    
    HK_HOLIDAYS_2025 = {
        "2025-01-01", "2025-01-29", "2025-01-30", "2025-01-31",
        "2025-04-04", "2025-04-18", "2025-04-21", "2025-05-01", "2025-05-05",
        "2025-05-31", "2025-07-01", "2025-10-01", "2025-10-07",
        "2025-12-25", "2025-12-26"
    }
    
    HK_HOLIDAYS_2026 = {
        "2026-01-01", "2026-02-17", "2026-02-18", "2026-02-19",
        "2026-04-03", "2026-04-06", "2026-04-25", "2026-05-01", "2026-05-24",
        "2026-06-19", "2026-07-01", "2026-10-01", "2026-10-26",
        "2026-12-25", "2026-12-26"
    }
    
    def __init__(self, provider: HKShortSellingProvider):
        """
        初始化调度器
        
        Args:
            provider: 沽空数据提供器
        """
        self.provider = provider
        self.scheduler = None
        self._running = False
        
        # 合并所有假期
        self.holidays = (
            self.HK_HOLIDAYS_2024 | 
            self.HK_HOLIDAYS_2025 | 
            self.HK_HOLIDAYS_2026
        )
    
    def start(self) -> None:
        """启动调度器"""
        if self._running:
            logger.warning("⚠️ [调度器] 已在运行中")
            return
        
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger
            
            self.scheduler = BackgroundScheduler(timezone="Asia/Hong_Kong")
            
            # 每个交易日 18:00 执行（收市后）
            trigger = CronTrigger(
                hour=18,
                minute=0,
                day_of_week="mon-fri",
                timezone="Asia/Hong_Kong"
            )
            
            self.scheduler.add_job(
                self._daily_job,
                trigger=trigger,
                id="hk_short_selling_daily",
                name="港股沽空数据每日采集"
            )
            
            self.scheduler.start()
            self._running = True
            
            logger.info("✅ [调度器] 已启动，每个交易日 18:00 执行")
            
        except ImportError:
            logger.error("❌ [调度器] 需要安装 apscheduler: pip install apscheduler")
        except Exception as e:
            logger.error(f"❌ [调度器] 启动失败: {e}")
    
    def stop(self) -> None:
        """停止调度器"""
        if self.scheduler and self._running:
            self.scheduler.shutdown()
            self._running = False
            logger.info("✅ [调度器] 已停止")
    
    def trigger_now(self) -> Dict:
        """
        立即触发采集任务
        
        Returns:
            采集结果
        """
        return self._daily_job()
    
    def _is_trading_day(self, date: datetime) -> bool:
        """
        判断是否为交易日
        
        Args:
            date: 日期
            
        Returns:
            是否为交易日
        """
        # 周末不是交易日
        if date.weekday() >= 5:
            return False
        
        # 检查是否为假期
        date_str = date.strftime("%Y-%m-%d")
        if date_str in self.holidays:
            return False
        
        return True
    
    def _daily_job(self) -> Dict:
        """
        每日采集任务
        
        Returns:
            采集结果
        """
        today = datetime.now()
        date_str = today.strftime("%Y-%m-%d")
        
        result = {
            "date": date_str,
            "success": False,
            "is_trading_day": False,
            "records_count": 0,
            "error": None
        }
        
        # 检查是否为交易日
        if not self._is_trading_day(today):
            logger.info(f"ℹ️ [每日采集] {date_str} 不是交易日，跳过")
            result["is_trading_day"] = False
            result["success"] = True
            return result
        
        result["is_trading_day"] = True
        
        try:
            records = self.provider.fetch_daily_data(date_str)
            result["records_count"] = len(records)
            result["success"] = True
            
            logger.info(f"✅ [每日采集] {date_str}: {len(records)} 条记录")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ [每日采集] {date_str} 失败: {e}")
        
        return result


# ============================================================================
# 风控分析工具
# ============================================================================

def get_short_selling_risk_analysis(
    provider: HKShortSellingProvider,
    stock_code: str,
    date: str = None,
    risk_threshold: float = 0.10,
    history_days: int = 20
) -> Dict:
    """
    获取沽空数据风险分析
    
    Args:
        provider: 沽空数据提供器
        stock_code: 股票代码
        date: 分析日期，默认为今天
        risk_threshold: 风险阈值（默认 10%）
        history_days: 历史数据天数
        
    Returns:
        风险分析结果
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    normalized_code = stock_code.zfill(5)
    
    result = {
        "stock_code": normalized_code,
        "date": date,
        "has_data": False,
        "current_ratio": None,
        "is_high_risk": False,
        "risk_level": "未知",
        "trend": "未知",
        "trend_description": "",
        "history_avg": None,
        "history_max": None,
        "history_min": None,
        "analysis_text": ""
    }
    
    # 获取当日数据
    current_data = provider.get_stock_short_data(normalized_code, date)
    
    if not current_data:
        result["analysis_text"] = f"⚠️ 未找到 {normalized_code} 在 {date} 的沽空数据"
        return result
    
    result["has_data"] = True
    result["current_ratio"] = current_data.get("short_ratio", 0)
    
    # 判断是否高风险
    current_ratio = result["current_ratio"]
    result["is_high_risk"] = current_ratio > risk_threshold
    
    # 风险等级
    if current_ratio > 0.30:
        result["risk_level"] = "极高"
    elif current_ratio > 0.20:
        result["risk_level"] = "高"
    elif current_ratio > risk_threshold:
        result["risk_level"] = "中等"
    else:
        result["risk_level"] = "低"
    
    # 获取历史数据计算趋势
    end_date = datetime.strptime(date, "%Y-%m-%d")
    start_date = end_date - timedelta(days=history_days)
    
    history = provider.get_stock_short_history(
        normalized_code,
        start_date.strftime("%Y-%m-%d"),
        date
    )
    
    if history and len(history) > 1:
        ratios = [h.get("short_ratio", 0) for h in history]
        result["history_avg"] = sum(ratios) / len(ratios)
        result["history_max"] = max(ratios)
        result["history_min"] = min(ratios)
        
        # 计算趋势
        avg = result["history_avg"]
        if avg > 0:
            ratio_to_avg = current_ratio / avg
            
            if ratio_to_avg > 1.10:
                result["trend"] = "上升"
                result["trend_description"] = f"当前沽空比例高于历史平均 {(ratio_to_avg - 1) * 100:.1f}%"
            elif ratio_to_avg < 0.90:
                result["trend"] = "下降"
                result["trend_description"] = f"当前沽空比例低于历史平均 {(1 - ratio_to_avg) * 100:.1f}%"
            else:
                result["trend"] = "稳定"
                result["trend_description"] = "当前沽空比例接近历史平均水平"
    
    # 生成分析文本
    analysis_lines = [
        f"## 沽空风险分析 - {normalized_code}",
        f"",
        f"**分析日期**: {date}",
        f"**当前沽空比例**: {current_ratio * 100:.2f}%",
        f"**风险等级**: {result['risk_level']}",
        f"**趋势**: {result['trend']}",
    ]
    
    if result["history_avg"]:
        analysis_lines.extend([
            f"",
            f"### 历史数据（近 {history_days} 天）",
            f"- 平均沽空比例: {result['history_avg'] * 100:.2f}%",
            f"- 最高沽空比例: {result['history_max'] * 100:.2f}%",
            f"- 最低沽空比例: {result['history_min'] * 100:.2f}%",
        ])
    
    if result["is_high_risk"]:
        analysis_lines.extend([
            f"",
            f"### ⚠️ 风险提示",
            f"当前沽空比例 ({current_ratio * 100:.2f}%) 超过风险阈值 ({risk_threshold * 100:.0f}%)，",
            f"建议关注市场情绪变化和潜在下行风险。"
        ])
    
    if result["trend_description"]:
        analysis_lines.extend([
            f"",
            f"### 趋势分析",
            result["trend_description"]
        ])
    
    result["analysis_text"] = "\n".join(analysis_lines)
    
    return result


def get_short_selling_market_analysis(
    provider: HKShortSellingProvider,
    stock_code: str,
    date: str = None,
    history_days: int = 20
) -> Dict:
    """
    获取沽空数据市场分析（供分析师代理使用）
    
    Args:
        provider: 沽空数据提供器
        stock_code: 股票代码
        date: 分析日期
        history_days: 历史数据天数
        
    Returns:
        市场分析结果
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    normalized_code = stock_code.zfill(5)
    
    result = {
        "stock_code": normalized_code,
        "date": date,
        "has_data": False,
        "short_shares": None,
        "short_value": None,
        "short_ratio": None,
        "trend": "未知",
        "market_sentiment": "中性",
        "sentiment_score": 0,
        "top_rank": None,
        "analysis_text": ""
    }
    
    # 获取当日数据
    current_data = provider.get_stock_short_data(normalized_code, date)
    
    if not current_data:
        result["analysis_text"] = f"⚠️ 未找到 {normalized_code} 在 {date} 的沽空数据"
        return result
    
    result["has_data"] = True
    result["short_shares"] = current_data.get("short_shares", 0)
    result["short_value"] = current_data.get("short_value", 0)
    result["short_ratio"] = current_data.get("short_ratio", 0)
    
    # 获取 Top 排名
    top_stocks = provider.get_top_short_stocks(date, 50)
    for i, stock in enumerate(top_stocks):
        if stock.get("stock_code") == normalized_code:
            result["top_rank"] = i + 1
            break
    
    # 获取历史数据计算趋势
    end_date = datetime.strptime(date, "%Y-%m-%d")
    start_date = end_date - timedelta(days=history_days)
    
    history = provider.get_stock_short_history(
        normalized_code,
        start_date.strftime("%Y-%m-%d"),
        date
    )
    
    current_ratio = result["short_ratio"]
    
    if history and len(history) > 1:
        ratios = [h.get("short_ratio", 0) for h in history]
        avg_ratio = sum(ratios) / len(ratios)
        
        if avg_ratio > 0:
            ratio_to_avg = current_ratio / avg_ratio
            
            if ratio_to_avg > 1.10:
                result["trend"] = "上升"
            elif ratio_to_avg < 0.90:
                result["trend"] = "下降"
            else:
                result["trend"] = "稳定"
    
    # 计算市场情绪
    # 沽空比例越高，看空情绪越强
    if current_ratio > 0.25:
        result["market_sentiment"] = "强烈看空"
        result["sentiment_score"] = -2
    elif current_ratio > 0.15:
        result["market_sentiment"] = "偏空"
        result["sentiment_score"] = -1
    elif current_ratio > 0.08:
        result["market_sentiment"] = "中性"
        result["sentiment_score"] = 0
    elif current_ratio > 0.03:
        result["market_sentiment"] = "偏多"
        result["sentiment_score"] = 1
    else:
        result["market_sentiment"] = "强烈看多"
        result["sentiment_score"] = 2
    
    # 生成分析文本
    analysis_lines = [
        f"## 沽空市场分析 - {normalized_code}",
        f"",
        f"**分析日期**: {date}",
        f"",
        f"### 沽空指标",
        f"- 沽空股数: {result['short_shares']:,} 股",
        f"- 沽空金额: HK${result['short_value']:,.2f}",
        f"- 沽空比例: {current_ratio * 100:.2f}%",
    ]
    
    if result["top_rank"]:
        analysis_lines.append(f"- 沽空排名: 第 {result['top_rank']} 名")
    
    analysis_lines.extend([
        f"",
        f"### 市场情绪",
        f"- 情绪判断: {result['market_sentiment']}",
        f"- 趋势方向: {result['trend']}",
    ])
    
    # 情绪解读
    sentiment_interpretation = {
        "强烈看空": "市场对该股票持强烈看空态度，沽空活动非常活跃，需警惕下行风险。",
        "偏空": "市场对该股票偏向看空，沽空比例较高，建议谨慎操作。",
        "中性": "市场对该股票态度中性，沽空活动处于正常水平。",
        "偏多": "市场对该股票偏向看多，沽空比例较低，市场情绪相对乐观。",
        "强烈看多": "市场对该股票持强烈看多态度，沽空活动很少，市场情绪非常乐观。"
    }
    
    analysis_lines.extend([
        f"",
        f"### 情绪解读",
        sentiment_interpretation.get(result["market_sentiment"], "")
    ])
    
    result["analysis_text"] = "\n".join(analysis_lines)
    
    return result


# ============================================================================
# 全局实例和便捷函数
# ============================================================================

_provider_instance: Optional[HKShortSellingProvider] = None
_scheduler_instance: Optional[ShortSellingScheduler] = None


def get_short_selling_provider() -> HKShortSellingProvider:
    """获取沽空数据提供器全局实例"""
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = HKShortSellingProvider()
    return _provider_instance


def get_short_selling_scheduler() -> ShortSellingScheduler:
    """获取沽空数据调度器全局实例"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ShortSellingScheduler(get_short_selling_provider())
    return _scheduler_instance


def init_short_selling_module(mongodb_client=None, redis_client=None):
    """
    初始化沽空数据模块
    
    Args:
        mongodb_client: MongoDB 客户端
        redis_client: Redis 客户端
    """
    provider = get_short_selling_provider()
    
    if mongodb_client:
        provider.set_mongodb_client(mongodb_client)
    
    if redis_client:
        provider.set_redis_client(redis_client)
    
    logger.info("✅ [沽空模块] 初始化完成")


# 便捷函数
def fetch_short_selling_data(date: str) -> List[ShortSellingRecord]:
    """获取指定日期的沽空数据"""
    return get_short_selling_provider().fetch_daily_data(date)


def get_stock_short_info(stock_code: str, date: str = None) -> Optional[Dict]:
    """获取股票沽空信息"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    return get_short_selling_provider().get_stock_short_data(stock_code, date)


def get_top_short_stocks(date: str = None, top_n: int = 20) -> List[Dict]:
    """获取沽空比例最高的股票"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    return get_short_selling_provider().get_top_short_stocks(date, top_n)


def analyze_short_selling_risk(stock_code: str, date: str = None) -> Dict:
    """分析股票沽空风险"""
    return get_short_selling_risk_analysis(
        get_short_selling_provider(),
        stock_code,
        date
    )


def analyze_short_selling_market(stock_code: str, date: str = None) -> Dict:
    """分析股票沽空市场情绪"""
    return get_short_selling_market_analysis(
        get_short_selling_provider(),
        stock_code,
        date
    )


# 模块导出
__all__ = [
    # 数据模型
    "ShortSellingRecord",
    
    # 核心组件
    "HKEXShortSellingParser",
    "ShortSellingRepository",
    "ShortSellingCache",
    "RateLimiter",
    "HKShortSellingProvider",
    "ShortSellingScheduler",
    
    # 分析函数
    "get_short_selling_risk_analysis",
    "get_short_selling_market_analysis",
    
    # 全局实例
    "get_short_selling_provider",
    "get_short_selling_scheduler",
    "init_short_selling_module",
    
    # 便捷函数
    "fetch_short_selling_data",
    "get_stock_short_info",
    "get_top_short_stocks",
    "analyze_short_selling_risk",
    "analyze_short_selling_market",
]
