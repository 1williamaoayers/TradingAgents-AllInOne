
import asyncio
import aiohttp
import json
import os
from datetime import datetime

async def main():
    url = "http://172.20.0.1:9527/api/v1/news"
    # Limit to 10 per source to keep it reasonable but comprehensive
    params = {"keyword": "小米集团", "limit": 10}
    output_file = "/app/results/01810.HK/2026-01-19/reports/Playwright_Raw.md"
    
    print(f"Requesting data from {url}...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params, timeout=300) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get("data", [])
                    metadata = data.get("metadata", {})
                    
                    print(f"Got {len(results)} items. Saving to {output_file}...")
                    
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(f"# Playwright News Data (Raw Output)\n\n")
                        f.write(f"> **Generate Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"> **Keyword**: {params['keyword']}\n")
                        f.write(f"> **Total Items**: {len(results)}\n")
                        f.write(f"> **Duration**: {metadata.get('duration_seconds')}s\n")
                        f.write(f"> **Sources**: {', '.join(metadata.get('sources_used', []))}\n\n")
                        
                        f.write(f"---\n\n")
                        
                        for i, item in enumerate(results, 1):
                            title = item.get('title', 'No Title')
                            source = item.get('source', 'Unknown')
                            time = item.get('publish_time', 'N/A')
                            url = item.get('url', '#')
                            content = item.get('content', '') or item.get('summary', '') or 'No content'
                            
                            f.write(f"## {i}. {title}\n")
                            f.write(f"- **Source**: {source} | **Time**: {time}\n")
                            f.write(f"- **Link**: [{url}]({url})\n\n")
                            f.write(f"{content[:300]}...\n\n") # Truncate long content
                            f.write(f"---\n\n")
                            
                    print("✅ Success.")
                else:
                    print(f"❌ Failed with status {response.status}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
