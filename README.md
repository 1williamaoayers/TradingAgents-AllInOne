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
git clone -b dev https://github.com/1williamaoayers/TradingAgents-AllInOne.git

# (可选) 如果网络不佳，可临时指定代理 (将 127.0.0.1:7890 替换为您的实际代理地址)
# git clone -b dev -c http.proxy=http://127.0.0.1:7890 https://github.com/1williamaoayers/TradingAgents-AllInOne.git

cd TradingAgents-AllInOne
```

### 2. 🛡️ 终极防丢脸方案 (Codespaces)
**如果您的电脑没有 Docker，或者网络很卡，请直接点击下方按钮：**

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/1williamaoayers/TradingAgents-AllInOne)

> **云端运行说明**: 点击后会自动为您启动一个云端 Linux 环境，内置所有依赖。进入后在终端输入 `docker-compose up -d` 即可。

### 3. ⚡ 一键启动 (本地部署)

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
| **API** | `ta-app` | 8000 | FastAPI 后端 (容器内部) |
| **Scraper** | `ta-scraper` | 9527 | PlaywriteOCR 爬虫 API |
| **DB** | `ta-mongodb` | 27017 | MongoDB 数据库 |
| **Cache** | `ta-redis` | 6379 | Redis 缓存 |

---

## 🔄 更新方法

```bash
docker-compose pull
docker-compose up -d
```

***


### 🚀 从零开始部署 (小白一键粘贴版)
如果您是第一次部署，请直接复制下面整段命令（包含下载、配置、修复权限、启动）：

```bash
# 0. 准备工作 (确保安装了 git 和 docker)
# sudo apt update && sudo apt install -y git

# 1. 下载项目 (默认使用 dev 开发分支)
git clone -b dev https://github.com/1williamaoayers/TradingAgents-AllInOne.git

# 2. 进入目录
cd TradingAgents-AllInOne

# 3. 初始化配置
if [ ! -f .env ]; then
    cp .env.example .env
    echo "配置文件 .env 已创建"
fi

# 4. 暴力修复权限 (关键！解决 Permission denied)
chmod 666 .env
mkdir -p config
chmod -R 777 config

# 5. 启动服务
docker-compose up -d
```

***

### 🛠️ 备用方案（手动 SSH 修复 - 针对已存在项目）
如果 `start.sh` 无法运行，请直接复制粘贴以下命令（解决权限与启动问题）：

```bash
# 1. 进入项目目录
cd /home/TradingAgents-AllInOne

# 2. 拉取最新代码
git pull

# 3. 暴力修复权限 (小白专用，解决 Permission denied)
chmod 666 .env
mkdir -p config
chmod -R 777 config

# 4. 启动服务
docker-compose up -d
```
