#!/usr/bin/env python3
"""
TradingAgents-CN 核心模块

这是一个基于多智能体的股票分析系统，支持A股、港股和美股的综合分析。
"""
import requests
import yfinance.data

# 💉 注入 "朴实无华" 的 Chrome 伪装头 (Global Patch)
# 目的: 彻底解决 Yahoo Finance 429 限流及 Docker SSL 兼容性问题
def patch_yfinance_headers():
    # 1. 定义一个带伪装头的 Session
    class ChromeSession(requests.Session):
        def __init__(self, **kwargs):
            # 兼容性处理：如果有人传了 impersonate 参数 (curl_cffi legacy)，直接忽略
            kwargs.pop('impersonate', None) 
            super().__init__(**kwargs)
            # 核心：伪装成 Chrome 浏览器 (Windows)
            self.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            })

    # 2. 告诉 yfinance 使用这个 Session
    yfinance.data.requests.Session = ChromeSession

# 🚀 立即执行 Patch
patch_yfinance_headers()


__version__ = "1.0.0-preview"
__author__ = "TradingAgents-CN Team"
__description__ = "Multi-agent stock analysis system for Chinese markets"

# 导入核心模块
try:
    from .config import config_manager
    from .utils import logging_manager
except ImportError:
    # 如果导入失败，不影响模块的基本功能
    pass

__all__ = [
    "__version__",
    "__author__", 
    "__description__"
]