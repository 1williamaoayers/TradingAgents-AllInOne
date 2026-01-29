# sitecustomize.py - Auto-injected by Docker Volume
# 同时兼容 yfinance 和 AKShare 的 curl_cffi 问题
import sys
import types
import logging
import os

# ==================== Part 1: Patch yfinance ====================
try:
    import requests
    import yfinance.data
    
    logging.info("🐵 sitecustomize: Applying yfinance Monkey Patch...")

    class SafeSession(requests.Session):
        def __init__(self, **kwargs):
            kwargs.pop('impersonate', None)
            kwargs.pop('thread', None)  # 兼容 curl_cffi 0.13.0
            super().__init__(**kwargs)
            self.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
            })

    fake_requests = types.ModuleType("fake_requests")
    for name in dir(requests):
        if not name.startswith("__"):
            setattr(fake_requests, name, getattr(requests, name))

    fake_requests.Session = SafeSession
    if not hasattr(fake_requests.exceptions, 'DNSError'):
        fake_requests.exceptions.DNSError = requests.exceptions.ConnectionError

    fake_session_mod = types.ModuleType("session")
    fake_session_mod.Session = SafeSession
    fake_requests.session = fake_session_mod

    yfinance.data.requests = fake_requests
    print("✅ sitecustomize: yfinance patched successfully.")

except Exception as e:
    print(f"⚠️ sitecustomize: yfinance patch skipped: {e}")


# ==================== Part 2: Patch curl_cffi for AKShare ====================
try:
    from curl_cffi import requests as curl_requests
    
    _OriginalCurlSession = curl_requests.Session
    
    class PatchedCurlSession(_OriginalCurlSession):
        """兼容 curl_cffi 0.13.0 的 Session，移除不支持的 thread 参数"""
        def __init__(self, *args, **kwargs):
            # 移除 curl_cffi 0.13.0 不再支持的参数
            kwargs.pop('thread', None)
            super().__init__(*args, **kwargs)
    
    # 替换 curl_cffi.requests.Session
    curl_requests.Session = PatchedCurlSession
    
    # 同时替换 curl_cffi.Session（有些代码直接 from curl_cffi import Session）
    import curl_cffi
    curl_cffi.Session = PatchedCurlSession
    curl_cffi.requests.Session = PatchedCurlSession
    
    print("✅ sitecustomize: curl_cffi patched successfully (thread param removed).")

except ImportError:
    print("⚠️ sitecustomize: curl_cffi not installed, skipping patch.")
except Exception as e:
    print(f"⚠️ sitecustomize: curl_cffi patch failed: {e}")
