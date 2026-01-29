#!/usr/bin/env python3
"""
Alpha Vantage新闻工具 - 修复版
增加限流保护和更好的错误处理
"""

import logging
import requests
import os
import time
from datetime import datetime

logger = logging.getLogger(__name__)

# 限流控制
_last_request_time = 0
_request_count = 0
_request_count_reset_time = 0
MIN_REQUEST_INTERVAL = 15  # 每次请求间隔至少15秒（免费版限制5次/分钟）
MAX_REQUESTS_PER_DAY = 25  # 每天最多25次（保守值，免费版500次但分配给多个股票）


def get_alpha_vantage_news(ticker: str, limit: int = 15):
    """
    获取Alpha Vantage个股新闻
    
    Args:
        ticker: 股票代码（09618, AAPL等）
        limit: 最大新闻数量
    
    Returns:
        list: 新闻列表
    """
    global _last_request_time, _request_count, _request_count_reset_time
    
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        logger.error("[Alpha Vantage] API Key未配置")
        return []
    
    # 检查每日配额
    current_time = time.time()
    if current_time - _request_count_reset_time > 86400:  # 24小时重置
        _request_count = 0
        _request_count_reset_time = current_time
    
    if _request_count >= MAX_REQUESTS_PER_DAY:
        logger.warning(f"[Alpha Vantage] 已达每日配额限制 ({MAX_REQUESTS_PER_DAY})")
        return []

    # 限流：确保请求间隔
    time_since_last = current_time - _last_request_time
    if time_since_last < MIN_REQUEST_INTERVAL:
        wait_time = MIN_REQUEST_INTERVAL - time_since_last
        logger.info(f"[Alpha Vantage] 限流等待 {wait_time:.1f}秒...")
        time.sleep(wait_time)
    
    url = "https://www.alphavantage.co/query"
    params = {
        'function': 'NEWS_SENTIMENT',
        'tickers': ticker,
        'apikey': api_key,
        'limit': limit,
        'sort': 'LATEST'
    }
    
    try:
        logger.info(f"[Alpha Vantage] 请求个股新闻: {ticker}, limit={limit}")
        _last_request_time = time.time()
        _request_count += 1
        
        response = requests.get(url, params=params, timeout=30)
        
        # 检查HTTP状态
        if response.status_code != 200:
            logger.error(f"[Alpha Vantage] HTTP错误: {response.status_code}")
            return []
        
        # 检查响应内容
        content = response.text.strip()
        if not content:
            logger.error("[Alpha Vantage] 响应为空（可能被限流）")
            return []
        
        # 尝试解析JSON
        try:
            data = response.json()
        except Exception as json_err:
            logger.error(f"[Alpha Vantage] JSON解析失败: {json_err}")
            logger.error(f"[Alpha Vantage] 响应内容前200字符: {content[:200]}")
            return []

        # 检查API错误
        if 'Error Message' in data:
            logger.error(f"[Alpha Vantage] API错误: {data['Error Message']}")
            return []
        
        # 检查限流提示
        if 'Note' in data:
            logger.warning(f"[Alpha Vantage] API限流: {data['Note']}")
            return []
        
        if 'Information' in data:
            logger.warning(f"[Alpha Vantage] API提示: {data['Information']}")
            return []
        
        if 'feed' in data:
            news_items = data['feed']
            logger.info(f"[Alpha Vantage] ✅ 返回{len(news_items)}条新闻")
            
            # 格式化新闻
            formatted_news = []
            for item in news_items:
                ticker_sentiment = None
                if 'ticker_sentiment' in item:
                    for ts in item['ticker_sentiment']:
                        if ts.get('ticker', '').upper() == ticker.upper():
                            ticker_sentiment = ts.get('ticker_sentiment_label', 'Neutral')
                            break
                
                formatted_news.append({
                    'title': item.get('title', '无标题'),
                    'summary': item.get('summary', ''),
                    'source': item.get('source', '未知来源'),
                    'url': item.get('url', ''),
                    'time_published': item.get('time_published', ''),
                    'sentiment': ticker_sentiment or item.get('overall_sentiment_label', 'Neutral'),
                    'relevance_score': item.get('relevance_score', 0)
                })
            
            return formatted_news
        else:
            logger.warning(f"[Alpha Vantage] 未返回新闻数据，响应keys: {list(data.keys())}")
            return []

    except requests.exceptions.Timeout:
        logger.error("[Alpha Vantage] 请求超时")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"[Alpha Vantage] 网络请求失败: {e}")
        return []
    except Exception as e:
        logger.error(f"[Alpha Vantage] 处理失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []


def format_alpha_vantage_news(news_items, stock_code):
    """格式化Alpha Vantage新闻为markdown"""
    if not news_items:
        return ""
    
    report = f"# {stock_code} 个股新闻 (Alpha Vantage)\n\n"
    report += f"📅 查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += f"📊 新闻数量: {len(news_items)} 条\n\n"
    
    for i, news in enumerate(news_items, 1):
        title = news.get('title', '无标题')
        summary = news.get('summary', '')
        source = news.get('source', '未知来源')
        time_published = news.get('time_published', '')
        sentiment = news.get('sentiment', 'Neutral')
        
        if time_published:
            try:
                dt = datetime.strptime(time_published, '%Y%m%dT%H%M%S')
                time_str = dt.strftime('%Y-%m-%d %H:%M')
            except:
                time_str = time_published
        else:
            time_str = '未知时间'
        
        sentiment_icon = {
            'Bullish': '📈', 'Bearish': '📉', 'Neutral': '➖',
            'Somewhat-Bullish': '📊', 'Somewhat-Bearish': '📉'
        }.get(sentiment, '➖')
        
        report += f"## {i}. {sentiment_icon} {title}\n\n"
        report += f"**来源**: {source} | **时间**: {time_str}\n"
        report += f"**情绪**: {sentiment}\n\n"
        
        if summary:
            summary_text = summary[:500] + '...' if len(summary) > 500 else summary
            report += f"{summary_text}\n\n"
        
        report += "---\n\n"
    
    return report
