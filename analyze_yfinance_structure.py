#!/usr/bin/env python3
"""分析yfinance返回的新闻数据结构"""
import sys
sys.path.insert(0, '/app')
import json

print("=" * 60)
print("分析 yfinance 1810.HK 返回的新闻数据结构")
print("=" * 60)

import yfinance as yf

ticker = yf.Ticker("1810.HK")
news_list = ticker.news

print(f"\n📊 基本信息:")
print(f"  - 数据类型: {type(news_list)}")
print(f"  - 新闻数量: {len(news_list)}")
print(f"  - 是否为空: {not news_list}")

if news_list and len(news_list) > 0:
    print(f"\n📰 第1条新闻的完整结构:")
    first_news = news_list[0]
    print(json.dumps(first_news, indent=2, ensure_ascii=False))
    
    print(f"\n🔑 第1条新闻的顶层键:")
    print(f"  {list(first_news.keys())}")
    
    if 'content' in first_news:
        print(f"\n📄 content字段的键:")
        print(f"  {list(first_news['content'].keys())}")
    
    print(f"\n📋 所有新闻的标题列表:")
    for i, news in enumerate(news_list, 1):
        title = news.get('content', {}).get('title', 'N/A')
        pub_date = news.get('content', {}).get('pubDate', 'N/A')
        provider = news.get('content', {}).get('provider', {}).get('displayName', 'N/A')
        print(f"  [{i}] {title}")
        print(f"      来源: {provider} | 发布: {pub_date}")
    
    print(f"\n🔍 数据字段分析:")
    sample = news_list[0]['content']
    print(f"  - 标题字段: 'title' = {sample.get('title', 'N/A')[:50]}...")
    print(f"  - 摘要字段: 'summary' = {sample.get('summary', 'N/A')[:50]}...")
    print(f"  - 链接字段: 'canonicalUrl' = {sample.get('canonicalUrl', {}).get('url', 'N/A')}")
    print(f"  - 发布时间: 'pubDate' = {sample.get('pubDate', 'N/A')}")
    print(f"  - 来源: 'provider.displayName' = {sample.get('provider', {}).get('displayName', 'N/A')}")
    
    print(f"\n✅ 结论: yfinance返回的是包含完整新闻对象的列表")
    print(f"   每条新闻包含: id, content(title, summary, pubDate, provider, canonicalUrl等)")

print("\n" + "=" * 60)
