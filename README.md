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

## 🛠️ 极简部署 (推荐)

**无需代码，无需脚本，无需 Git。**

### 1. 准备文件

**方式 A：直接下载 (适合有图形界面的电脑)**
1. [docker-compose.yml](https://github.com/1williamaoayers/TradingAgents-AllInOne/blob/dev/docker-compose.yml)
2. [.env.example](https://github.com/1williamaoayers/TradingAgents-AllInOne/blob/dev/.env.example) (下载后重命名为 `.env`)

**方式 B：SSH 终端一键生成 (适合 VPS/云服务器)**
*复制下方整段命令，在终端粘贴回车即可：*

```bash
# 1. 创建目录
mkdir -p trading-agents && cd trading-agents

# 2. 生成配置文件
cat > .env <<EOF
# 基础配置
MONGODB_USERNAME=admin
MONGODB_PASSWORD=tradingagents123
REDIS_PASSWORD=tradingagents123
EOF

cat > docker-compose.yml <<EOF
version: '3.8'

services:
  # ==========================================
  # MongoDB 数据库
  # ==========================================
  mongodb:
    image: mongo:4.4
    container_name: ta-mongodb
    restart: unless-stopped
    ports:
      - "27017:27017"
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=tradingagents123
      - TZ=Asia/Shanghai
    volumes:
      - mongodb_data:/data/db
    command: >
      mongod --wiredTigerCacheSizeGB 0.25 --setParameter diagnosticDataCollectionEnabled=false
    deploy:
      resources:
        limits:
          memory: 512M
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongo localhost:27017/test --quiet
      interval: 60s
      timeout: 10s
      retries: 3

  # ==========================================
  # Redis 缓存
  # ==========================================
  redis:
    image: redis:7-alpine
    container_name: ta-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    command: >
      redis-server --requirepass tradingagents123 --maxmemory 50mb --maxmemory-policy allkeys-lru
    deploy:
      resources:
        limits:
          memory: 128M
    healthcheck:
      test: [ "CMD", "redis-cli", "-a", "tradingagents123", "ping" ]
      interval: 60s
      timeout: 10s
      retries: 3

  # ==========================================
  # PlaywriteOCR 爬虫服务
  # ==========================================
  playwriteocr:
    image: ghcr.io/1williamaoayers/playwriteocr:latest
    container_name: ta-scraper
    restart: unless-stopped
    ports:
      - "9527:9527"
    deploy:
      resources:
        limits:
          memory: 1G
    healthcheck:
      test: [ "CMD", "curl", "-f", "http://localhost:9527/api/v1/health" ]
      interval: 60s
      timeout: 10s
      retries: 3

  # ==========================================
  # TradingAgents 主应用
  # ==========================================
  tradingagents:
    image: ghcr.io/1williamaoayers/tradingagents-allinone:dev
    container_name: ta-app
    restart: unless-stopped
    ports:
      - "8501:8501"
    volumes:
      - ta_data:/app/data
      - ta_logs:/app/logs
      - ./.env:/app/.env
    env_file:
      - .env
    environment:
      - TZ=Asia/Shanghai
      - MONGODB_HOST=mongodb
      - MONGODB_PORT=27017
      - MONGODB_USERNAME=admin
      - MONGODB_PASSWORD=tradingagents123
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=tradingagents123
      - SCRAPER_API_URL=http://playwriteocr:9527
    deploy:
      resources:
        limits:
          memory: 1G
    depends_on:
      mongodb:
        condition: service_healthy
      redis:
        condition: service_healthy
      playwriteocr:
        condition: service_healthy
    healthcheck:
      test: [ "CMD", "curl", "-f", "http://localhost:8501/_stcore/health" ]
      interval: 60s
      timeout: 10s
      retries: 3

volumes:
  mongodb_data:
  redis_data:
  ta_data:
  ta_logs:
EOF
```

### 2. 启动服务
在文件夹内打开终端（Windows 用户按住 Shift 右键选择"在终端打开"），运行：

```bash
docker-compose up -d
```

等待镜像下载完成即可。系统会自动拉取包含最新数据（含港股名称库）的镜像。

### 3. 访问
打开浏览器访问：`http://localhost:8501`

---

## 💾 数据管理
部署后文件夹内会自动生以下目录，**请勿删除**：
- `ta_data/`: 应用数据（配置、自选股等）
- `mongodb_data/`: 数据库文件
- `redis_data/`: 缓存数据

---

## 🔄 更新方法
在文件夹内运行：
```bash
docker-compose pull
docker-compose up -d
```
系统会自动从云端拉取最新镜像并重启，数据不会丢失。
