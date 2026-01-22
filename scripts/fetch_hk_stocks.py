
import os
import sys
import pandas as pd
import akshare as ak
from pymongo import MongoClient
import time
from datetime import datetime

# 连接到底层 AKShare (需要在容器内运行或安装了akshare的环境)
# 如果本地没有akshare，此脚本应在docker容器内运行

def fetch_and_cache_hk_stocks():
    print("🚀 开始获取港股列表...")
    
    try:
        # 获取港股列表 (使用 akshare)
        # stock_hk_spot_em 接口返回所有港股实时行情，包含代码和名称
        df = ak.stock_hk_spot_em()
        print(f"✅ 成功获取 {len(df)} 只港股数据")
        
        # 准备数据
        # DataFrame 列名: 序号, 代码, 名称, ...
        # 我们只需要 '代码' 和 '名称'
        
        stocks_to_cache = []
        for index, row in df.iterrows():
            code = str(row['代码'])
            name = str(row['名称'])
            
            # 标准化代码 (移除前导零? 不，港股通常保留5位)
            # AKShare 返回的是 '00700' 这样的5位代码
            
            stocks_to_cache.append({
                "code": code,
                "name": name,
                "market": "HK",
                "updated_at": datetime.utcnow()
            })
            
        # 连接 MongoDB
        mongo_uri = os.getenv("MONGO_URI", "mongodb://admin:tradingagents123@mongodb:27017/?authSource=admin")
        # 兼容脚本直接运行时的 localhost 情况 (如果是从容器外)
        if "mongodb" in mongo_uri and "OS" in os.environ and "Windows" in os.environ["OS"]: 
             # 简单的本地调试兼容
             pass 

        print(f"🔌 连接数据库: {mongo_uri}")
        client = MongoClient(mongo_uri)
        db = client["tradingagents"]
        collection = db["stock_names_cache"]
        
        # 批量写入 (使用 update_one upsert 方式防止重复，或 delete_many + insert_many)
        # 为了效率，这里使用 bulk_write 或简单的循环 update
        
        print("💾 正在写入数据库缓存...")
        
        from pymongo import UpdateOne
        operations = []
        for stock in stocks_to_cache:
            operations.append(
                UpdateOne(
                    {"code": stock["code"]},
                    {"$set": stock},
                    upsert=True
                )
            )
            
        if operations:
            result = collection.bulk_write(operations)
            print(f"✅ 缓存更新完成! 匹配: {result.matched_count}, 修改: {result.modified_count}, 插入: {result.upserted_count}")
        
        # 验证一下 Xiaomi (01810)
        xiaomi = collection.find_one({"code": "01810"})
        if xiaomi:
            print(f"🔍 验证: 01810 -> {xiaomi['name']}")
        else:
            print("⚠️ 警告: 未找到 01810 (小米集团)")
            
        client.close()
        
    except Exception as e:
        print(f"❌ 获取或缓存失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fetch_and_cache_hk_stocks()
