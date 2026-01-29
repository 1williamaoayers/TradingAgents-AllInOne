# TradingAgents-CN 一键部署版

基于多智能体的股票分析系统，支持 A股、港股、美股 综合分析。

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/1williamaoayers/TradingAgents-AllInOne.git
cd TradingAgents-AllInOne
git checkout dev
```

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥
```

### 3. 启动服务
```bash
docker compose up -d
```

### 4. 访问 Web UI
打开浏览器访问: http://localhost:8501

---

## 📋 API 密钥申请指南

| 服务 | 用途 | 申请地址 |
|------|------|----------|
| DeepSeek | AI 模型 | https://platform.deepseek.com/ |
| 阿里云 | AI 模型(备选) | https://dashscope.console.aliyun.com/ |
| Finnhub | 股票数据 | https://finnhub.io/ |
| Alpha Vantage | 历史数据 | https://www.alphavantage.co/support/#api-key |
| Serper | 新闻搜索 | https://serper.dev/ |

---

## 🐳 服务架构

| 服务 | 端口 | 说明 |
|------|------|------|
| tradingagents | 8501 | Web UI (Streamlit) |
| mongodb | 27017 | 数据存储 |
| redis | 6379 | 缓存 |
| rsshub | 1200 | 自建 RSS 服务 |
| playwriteocr | 9527 | 网页爬虫 |

---

## 🔧 常用命令

```bash
# 查看日志
docker compose logs -f tradingagents

# 重启服务
docker compose restart tradingagents

# 停止所有服务
docker compose down

# 清理数据重新开始
docker compose down -v
```

---

## ⚠️ 系统要求

- Docker 20.10+
- Docker Compose 2.0+
- 内存: 最低 2GB，推荐 4GB
- 磁盘: 最低 5GB

---

## 📝 已知问题与修复

本版本已包含以下修复:
- ✅ yfinance 港股代码前导0问题
- ✅ curl_cffi 兼容性问题
- ✅ 新闻数据源优化

---

## 📄 License

MIT License
