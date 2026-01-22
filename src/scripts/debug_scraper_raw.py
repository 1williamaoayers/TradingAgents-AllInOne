
import asyncio
import aiohttp
import json
import os

async def main():
    print("# Debugging Scraper API Raw Response\n")
    
    # Direct API call to bypass adapter logic and see raw errors
    url = "http://172.20.0.1:9527/api/v1/news"
    params = {"keyword": "小米集团", "limit": 5}
    
    print(f"## Requesting: {url} with params {params}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params, timeout=300) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print("\n## Raw JSON Response keys:", data.keys())
                    
                    if not data.get("success"):
                         print(f"❌ API returned success=False: {data.get('error')}")
                    
                    results = data.get("data", [])
                    print(f"Data count: {len(results)}")
                    
                    metadata = data.get("metadata", {})
                    print(f"\n## Metadata:")
                    print(f"  - Duration: {metadata.get('duration_seconds')}s")
                    print(f"  - Sources Used: {metadata.get('sources_used')}")
                    
                    errors = metadata.get("errors")
                    if errors:
                        print(f"\n❌ ERRORS FOUND in metadata:")
                        for err in errors:
                            print(f"  - {err}")
                    else:
                        print("\n✅ No errors in metadata.")
                        
                else:
                    text = await response.text()
                    print(f"❌ Error response: {text}")
                    
        except Exception as e:
            print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
