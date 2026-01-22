
import asyncio
import os
import sys
from app.worker.news_adapters.scraper_adapter import ScraperAdapter
from tradingagents.utils.logging_init import get_logger

logger = get_logger("debug_scraper")

async def main():
    print("# Debugging Scraper Response\n")
    adapter = ScraperAdapter()
    
    # Test 1: Stock Code
    keyword_1 = "01810.HK"
    print(f"## Testing Keyword: '{keyword_1}'")
    try:
        news_1 = await adapter.get_news(keyword_1, limit=5)
        print(f"Result Count: {len(news_1)}")
        if not news_1:
            print("⚠️ No results found.")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "-"*30 + "\n")

    # Test 2: Company Name
    keyword_2 = "小米集团"
    print(f"## Testing Keyword: '{keyword_2}'")
    try:
        news_2 = await adapter.get_news(keyword_2, limit=20)
        print(f"Result Count: {len(news_2)}")
        
        if news_2:
            print("\n### Raw Data Preview:")
            for n in news_2:
                print(f"- **{n.get('title', 'No Title')}**")
                print(f"  - Source: {n.get('source')}")
                print(f"  - Time: {n.get('publish_time')}")
                print(f"  - URL: {n.get('url')}")
                print("")
            
            # Save correct report
            with open("/app/results/01810.HK/2026-01-19/reports/Playwright_Raw.md", "w") as f:
                f.write(f"# Playwright News Data (Raw Output)\n\n")
                f.write(f"> Scraped Keyword: {keyword_2}\n")
                f.write(f"> Total Count: {len(news_2)}\n\n")
                for n in news_2:
                    f.write(f"## {n.get('title')}\n")
                    f.write(f"- **Source**: {n.get('source')}\n")
                    f.write(f"- **Time**: {n.get('publish_time')}\n")
                    f.write(f"- **Content**: {n.get('content', '')[:200]}...\n\n")
            print("✅ Data saved to reports/Playwright_Raw.md")
            
        else:
            print("⚠️ No results found for company name either.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
