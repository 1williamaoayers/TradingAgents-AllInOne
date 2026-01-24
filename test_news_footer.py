
import os
import sys
import logging

# Ensure we can import from src
sys.path.append('/app')

from tradingagents.tools.unified_news_tool import UnifiedNewsAnalyzer
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_footer")

def test_news_footer():
    logger.info("🧪 Starting News Footer Test...")
    
    # Mock toolkit (can be empty for this test as we rely on internal logic or simple tools)
    class MockToolkit:
        pass
        
    analyzer = UnifiedNewsAnalyzer(MockToolkit())
    
    # Testing with a dummy stock code to trigger data fetching 
    # (Note: real fetching might fail, but we check if footer is appended even on partial/mock data)
    # Actually, we should try a real stock that might work, or rely on the tool handling failures gracefully
    # If network fails, result might be empty. 
    # Let's try to mock the internal methods if possible, or just call it and see.
    
    ticker = "01810.HK"
    logger.info(f"📊 Fetching news for {ticker}...")
    
    try:
        # We assume at least ONE source returns something or we get a fallback
        result = analyzer.get_stock_news_unified(ticker, max_news=5)
        
        content = result.get('content', '')
        logger.info(f"📄 Result Content Length: {len(content)}")
        
        if len(content) < 50:
            logger.warning("⚠️ Content too short, maybe data fetch failed completely.")
            print("SKIPPED: Data fetch failed")
            return

        # Check for footer
        current_date_str = datetime.now().strftime('%Y-%m-%d')
        expected_footer_part = f"*数据来源："
        expected_date_part = f"（截至{current_date_str}）*"
        
        if expected_footer_part in content and expected_date_part in content:
            print("✅ PASS: Footer found!")
            print(f"Footer Preview: {content[-100:]}")
        else:
            print("❌ FAIL: Footer NOT found!")
            print(f"Content Tail: {content[-200:]}")
            
    except Exception as e:
        logger.error(f"❌ Exception: {e}")
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_news_footer()
