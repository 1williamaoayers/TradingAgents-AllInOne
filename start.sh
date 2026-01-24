#!/bin/bash

# 设置颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}---------------------------------------------------${NC}"
echo -e "${GREEN} TradingAgents-CN 启动脚本 (Linux/Mac)${NC}"
echo -e "${GREEN}---------------------------------------------------${NC}"

# 检查 Docker 是否在运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${YELLOW}[ERROR] 未检测到 Docker 运行！${NC}"
    echo "请先安装 Docker 并确保已启动。"
    echo "下载地址: https://www.docker.com/products/docker-desktop/"
    exit 1
fi


# 检查并创建 .env
if [ ! -f .env ]; then
    echo -e "${YELLOW}[INFO] 未检测到配置文件，正在从模板创建...${NC}"
    cp .env.example .env
    echo -e "${GREEN}[SUCCESS] .env 文件已创建！请记得稍后在网页端或文件中填入API Key。${NC}"
else
    echo -e "${GREEN}[INFO] 检测到现有 .env 配置文件，将直接使用。${NC}"
fi

# 修复权限问题 (Docker 容器内非 root 用户需要写入权限)
echo -e "${YELLOW}[INFO] 正在调整文件权限以支持 Docker 容器写入...${NC}"
if [ -f .env ]; then
    chmod 666 .env
fi

if [ -d config ]; then
    chmod -R 777 config
else
    mkdir -p config
    chmod -R 777 config
fi

# 拉取镜像
echo -e "${YELLOW}[INFO] 正在拉取最新镜像...${NC}"
docker-compose pull

# 启动服务
echo -e "${YELLOW}[INFO] 正在启动服务...${NC}"
docker-compose up -d

echo -e "${GREEN}---------------------------------------------------${NC}"
echo -e "${GREEN}[SUCCESS] 服务启动成功！${NC}"
echo -e "请访问: ${YELLOW}http://localhost:8501${NC}"
echo -e "初始账号: ${YELLOW}admin${NC}"
echo -e "初始密码: ${YELLOW}admin123${NC}"
echo -e "${GREEN}---------------------------------------------------${NC}"
