# TradingAgents-CN 修复版镜像
# 基于官方镜像，打入多个兼容性补丁

FROM ghcr.io/1williamaoayers/tradingagents-allinone:dev

# 复制补丁文件
COPY patches/sitecustomize.py /home/appuser/.local/lib/python3.10/site-packages/sitecustomize.py
COPY patches/tradingagents_init_clean.py /app/tradingagents/__init__.py
COPY patches/yfinance_news_sync_service_fixed.py /app/app/worker/yfinance_news_sync_service.py
COPY patches/rss_adapter_fixed.py /app/app/worker/news_adapters/rss_adapter.py
COPY patches/alpha_vantage_news_fixed.py /app/tradingagents/tools/alpha_vantage_news.py
COPY patches/finnhub_adapter_fixed.py /app/app/worker/news_adapters/finnhub_adapter.py

# 确保权限正确
USER root
RUN chown appuser:appuser /home/appuser/.local/lib/python3.10/site-packages/sitecustomize.py \
    && chown appuser:appuser /app/tradingagents/__init__.py \
    && chown appuser:appuser /app/app/worker/yfinance_news_sync_service.py \
    && chown appuser:appuser /app/app/worker/news_adapters/rss_adapter.py \
    && chown appuser:appuser /app/tradingagents/tools/alpha_vantage_news.py \
    && chown appuser:appuser /app/app/worker/news_adapters/finnhub_adapter.py
USER appuser
