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
请在您的电脑上创建一个文件夹（例如 `trading-agents`），然后下载以下两个文件放入其中：

1. [docker-compose.yml](https://github.com/1williamaoayers/TradingAgents-AllInOne/blob/dev/docker-compose.yml)
2. [.env.example](https://github.com/1williamaoayers/TradingAgents-AllInOne/blob/dev/.env.example) (下载后重命名为 `.env`)

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
