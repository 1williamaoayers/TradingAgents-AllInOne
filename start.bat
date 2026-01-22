@echo off
chcp 65001 >nul
echo ---------------------------------------------------
echo  TradingAgents-CN 启动脚本 (Windows)
echo ---------------------------------------------------

if not exist .env (
    echo [INFO] 未检测到配置文件，正在从模板创建...
    copy .env.example .env >nul
    echo [SUCCESS] .env 文件已创建！请记得稍后在网页端或文件中填入API Key。
) else (
    echo [INFO] 检测到现有 .env 配置文件，将直接使用。
)

echo [INFO] 正在拉取最新镜像...
docker-compose pull

echo [INFO] 正在启动服务...
docker-compose up -d

echo ---------------------------------------------------
echo [SUCCESS] 服务启动成功！
echo 请访问: http://localhost:8501
echo 初始账号: admin
echo 初始密码: admin123
echo ---------------------------------------------------
pause
