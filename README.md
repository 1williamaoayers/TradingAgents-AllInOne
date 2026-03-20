# 🚀 TradingAgents All-In-One Deploy

> **📌 主分支** - 此为开发主分支，使用 `:latest` 镜像

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
2. [.env.example](https://github.com/1williamaoayers/TradingAgents-AllInOne/blob/dev/.env.example) (下载后请重命名为 `.env`)

**方式 B：SSH 终端一键生成 (适合 VPS/云服务器)**
*复制下方整段命令，在终端粘贴回车即可：*

```bash
# 1. 创建并进入目录
mkdir -p trading-agents && cd trading-agents

# 2. 下载配置文件 (使用 GitHub 源)
# 如果服务器无法访问 GitHub，请确保已配置网络环境
curl -o docker-compose.yml https://raw.githubusercontent.com/1williamaoayers/TradingAgents-AllInOne/dev/docker-compose.yml
curl -o .env https://raw.githubusercontent.com/1williamaoayers/TradingAgents-AllInOne/dev/.env.example

# 3. 设置权限 (防止权限问题导致配置无法保存)
chmod 666 .env

# 4. 启动服务
docker-compose up -d
```

> **💡 配置说明**:
> 启动后请直接在浏览器访问 `http://localhost:8501` -> **"配置管理"** 页面。
> 您在网页填写的 API Key 会**自动保存**回到这个 `.env` 文件中，并且同步到数据库，确保重启不丢失。

### 2. 启动服务
在文件夹内打开终端（Windows 用户按住 Shift 右键选择"在终端打开"），运行：

```bash
docker-compose up -d
```

等待镜像下载完成即可。系统会自动拉取包含最新数据（含港股名称库）的镜像。

### 3. 访问
打开浏览器访问：`http://localhost:8501`

---

## ⚠️ 常见踩坑

### 1. 容器间网络不通
**现象**：`Cannot connect to host playwriteocr:9527` 或 `mongodb:27017 Name or service not known`

**原因**：Docker 默认 bridge 网络**不提供**容器名 DNS 解析

**解决**：
- 确保 docker-compose.yml 中定义了自定义网络 `ta-network`
- **不要使用** `network_mode: bridge`，会让容器无法通过容器名互通

### 2. Scraper 连接失败
**现象**：爬虫同步超时

**原因**：`.env` 中 `SCRAPER_API_URL` 写成了错误的容器名

**解决**：确保 `.env` 中写的是 `SCRAPER_API_URL=http://ta-scraper:9527`（容器名是 `ta-scraper`，不是 `playwriteocr`）

### 3. MongoDB 连接失败
**原因**：Docker bridge 网络 DNS 不解析 `mongodb` 主机名

**解决**：
- 确保使用仓库默认的 docker-compose.yml（已配置自定义网络 `ta-network`）
- 如已部署过，先创建网络再重启：
  ```bash
  docker network create ta-network
  docker-compose down
  docker-compose up -d
  ```

### 4. A 股数据同步占用资源
**现象**：只想用港股，但系统同步了大量 A 股数据

**解决**：在 `.env` 中已默认禁用 A 股同步（见 `SYNC_STOCK_BASICS_ENABLED=false`），如需开启请修改此配置

---

## 💾 数据管理
部署后文件夹内会自动生成以下目录，**请勿删除**：
- `ta_data/`: 应用数据（配置、自选股等）
- `mongodb_data/`: 数据库文件

---

## 🔄 更新方法
在文件夹内运行：
```bash
docker-compose pull
docker-compose up -d
```
系统会自动从云端拉取最新镜像并重启，数据不会丢失。
