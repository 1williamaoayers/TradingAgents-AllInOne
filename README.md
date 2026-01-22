# 🚀 TradingAgents All-In-One Deploy

**一键部署 TradingAgents 全套服务**，包含主应用、MongoDB、Redis 和 PlaywriteOCR 爬虫。

专为懒人设计，无需配置网络，无需手动对接。

---

## ✨ 特性

- **全自动编排**：一个命令启动 4 个容器
- **内置集成**：主应用自动发现爬虫服务
- **数据持久化**：内置 Volume 自动管理数据
- **硬件兼容**：MongoDB 4.4 兼容所有 CPU (无AVX也能跑)
- **架构支持**：完美支持 ARM64 (树莓派/Mac) 和 AMD64

---

## 🛠️ 快速开始

### 1. 下载本仓库
```bash
git clone https://github.com/1williamaoayers/TradingAgents-AllInOne.git
cd TradingAgents-AllInOne
```

### 2. ⚡ 一键启动 (推荐)

**Windows 用户**:
双击运行 `start.bat`

**Mac/Linux 用户**:
```bash
chmod +x start.sh
./start.sh
```

> **自动配置说明**: 脚本会自动检测 `.env` 配置文件，如果不存在则自动创建，并拉取最新镜像启动服务。

### 3. (可选) 手动配置 & 启动
如果您更喜欢手动操作：
```bash
cp .env.example .env
# 编辑 .env 填入您的 API Key
docker-compose up -d
```

### 4. 访问服务
打开浏览器访问：`http://localhost:8501`

---

## 📊 服务清单

| 服务 | 容器名 | 端口 | 说明 |
|------|--------|------|------|
| **App** | `ta-app` | 8501 | Streamlit Web 界面 |
| **API** | `ta-app` | 8000 | FastAPI 后端 |
| **Scraper** | `ta-scraper` | 9527 | PlaywriteOCR 爬虫 API |
| **DB** | `ta-mongodb` | 27017 | MongoDB 数据库 |
| **Cache** | `ta-redis` | 6379 | Redis 缓存 |

---

## 🔄 更新方法

```bash
docker-compose pull
docker-compose up -d
```
