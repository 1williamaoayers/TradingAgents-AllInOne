
# sitecustomize.py - Auto-injected by Docker Volume
import sys
import types
import logging
import os

# Only patch if yfinance is likely to be used (optimization)
# But for safety, just patch. It's fast.

try:
    import requests
    # Ensure yfinance doesn't use curl_cffi by pre-import patching
    # But yfinance imports it unconditionally, so we must let it import, then SWAP.
    
    # We must lazily patch or patch immediately?
    # yfinance is not imported yet.
    # If we import yfinance here, we might trigger circular imports if yfinance imports other things.
    # But yfinance is usually a leaf or high level lib.
    
    import yfinance.data
    
    logging.info("🐵 sitecustomize: Applying yfinance Monkey Patch...")

    class SafeSession(requests.Session):
        def __init__(self, **kwargs):
            impersonate = kwargs.pop('impersonate', None)
            super().__init__(**kwargs)
            # 💉 Anti-Bot: Inject Real Browser Headers
            self.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            })
            if impersonate:
                pass # Silently ignore

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
    print(f"❌ sitecustomize: Failed to patch yfinance: {e}")
