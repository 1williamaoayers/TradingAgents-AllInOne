---
description: 安全部署与代码推送标准化流程 (防卡死版)
trigger_keywords: ["提交", "部署", "发布", "Deploy"]
---

# 🚀 安全部署流程 (Safe Deploy Workflow)

**核心目标**: 防止在日志刷屏的终端执行 Git 命令导致 Agent 系统崩溃。

## 1. 🛡️ 环境安全检查 (Environment Check)

### 防卡死协议（核心原则）

**核心原则**: 物理隔离环境 > 相信工具能力

在执行任何 Git 或部署命令前，必须执行此检查：

1.  **观察终端**: 当前终端是否有后台服务 (如 `apscheduler`, `docker compose logs -f`) 正在输出日志？
2.  **判断**:
    - [ ] **安静 (Quiet)**: 只有命令提示符，无跳动日志 -> **通过**，继续下一步。
    - [ ] **嘈杂 (Noisy)**: 有日志在刷新 -> **禁止操作**。

> ⚠️ **警告**: 如果终端嘈杂，必须执行以下任一操作：
> - `Ctrl+C` 停止当前服务。
> - 打开一个新的、干净的终端窗口。
> - 使用 `docker compose detach` 模式运行服务。

### 禁止行为

- ❌ **绝对禁止**：在有后台服务刷屏的终端执行 `git commit`, `git push` 等交互命令
- ❌ **绝对禁止**：在 `docker compose up` 的前台窗口执行其他命令

### 必须行为

1. **检查环境**：执行命令前，看终端是否有背景日志在跳动
2. **清理环境**：如果有，Ctrl+C 停止服务，或 `clear` 后确认静默
3. **开新窗口**：对于必须并行的任务，开启新的独立终端

## 2. 📦 代码提交 (Git Commit)

确保环境安静后，执行标准提交：

```bash
# 1. 查看状态 (确保无干扰)
git status

# 2. 添加文件
git add .

# 3. 提交 (附带清晰描述)
git commit -m "feat: [描述你的更改]"
```

## 3. ☁️ 推送代码 (Git Push)

```bash
# 推送到远程仓库
git push
```

## 4. 🚀 VPS 部署 (VPS Deployment)

如果是部署到 VPS，请遵循以下原则：

1.  **连接 VPS**: 使用干净的 SSH 会话。
2.  **拉取代码**: `git pull`
3.  **重启服务**:
    ```bash
    # 使用 restart 而不是 down/up，减少停机时间
    docker compose restart tradingagents
    
    # 如果有依赖更新
    docker compose up -d --build
    ```
4.  **验证状态**:
    ```bash
    docker ps
    docker logs --tail 20 tradingagents
    ```

## 5. ✅ 验证 (Verification)

部署完成后，必须验证服务是否恢复正常：
- 访问 Web 界面。
- 检查最近一条日志是否正常。
