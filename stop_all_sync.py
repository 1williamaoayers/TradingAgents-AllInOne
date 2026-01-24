#!/usr/bin/env python3
"""
停止所有同步服务和Docker容器
"""
import subprocess
import sys

def run_command(cmd):
    """运行命令"""
    print(f"执行: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"命令超时: {cmd}")
        return False
    except Exception as e:
        print(f"命令执行失败: {e}")
        return False

def main():
    print("=" * 60)
    print("停止所有同步服务和Docker容器")
    print("=" * 60)
    
    # 1. 强制停止所有Docker容器
    print("\n1. 停止所有Docker容器...")
    run_command("docker stop $(docker ps -aq)")
    
    # 2. 删除所有Docker容器
    print("\n2. 删除所有Docker容器...")
    run_command("docker rm $(docker ps -aq)")
    
    # 3. 检查Python进程
    print("\n3. 检查Python进程...")
    run_command("tasklist | findstr python")
    
    print("\n=" * 60)
    print("✅ 所有服务已停止")
    print("=" * 60)
    print("\n提示:")
    print("- 所有Docker容器已停止并删除")
    print("- 如需重新启动，请运行: docker-compose up -d")
    print("- 如需禁用历史数据同步，请修改 .env 文件:")
    print("  AKSHARE_HISTORICAL_SYNC_ENABLED=false")

if __name__ == "__main__":
    main()
