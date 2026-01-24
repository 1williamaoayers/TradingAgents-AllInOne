---
description: 命令安全执行协议 - 避免 Agent 因命令失败而卡死
---

# 命令安全执行协议 (Safe Command Execution)

## 🎯 目的
防止 Agent 因执行失败的命令而"傻等"导致软件卡死。

---

## 📋 核心规则

### 1. 短等待优先原则
- **首次执行**: 使用最短等待时间 (500-1000ms) 快速检测失败
- **确认成功后**: 再用适当的长等待时间获取完整输出

```
# ❌ 错误做法：直接长等待
WaitMsBeforeAsync: 10000  # 如果命令立即失败，白等10秒

# ✅ 正确做法：先短等待探测
WaitMsBeforeAsync: 500    # 快速发现错误
```

### 2. 命令预检 (Pre-flight Check)
对于不确定是否存在的命令，先验证：

```bash
# Docker 容器内命令检查
docker exec <container> which <command>
# 或
docker exec <container> command -v <command>
```

---

## ⚠️ 已知兼容性问题

### MongoDB Shell
| 版本 | Shell 命令 | 备注 |
|------|-----------|------|
| 4.4 及以下 | `mongo` | 老版本 shell |
| 5.0+ | `mongosh` | 新版本 shell |

**正确用法**:
```bash
# MongoDB 4.4
docker exec ta-mongodb mongo --quiet --eval "db.stats()"

# MongoDB 5.0+
docker exec ta-mongodb mongosh --quiet --eval "db.stats()"
```

### Docker Compose
| 版本 | 命令 |
|------|------|
| V1 (旧) | `docker-compose` |
| V2 (新) | `docker compose` |

---

## 🔄 标准执行流程

### 步骤 1: 预检 (500ms)
```bash
docker exec <container> which <command>
```
- 成功 → 继续步骤2
- 失败 → 检查替代命令或报告问题

### 步骤 2: 执行 (根据任务调整)
- 简单查询: 1000-3000ms
- 数据处理: 5000-10000ms
- 构建/部署: 使用后台模式 + 轮询

### 步骤 3: 验证
检查退出码和输出，确认执行成功。

---

## 🛡️ 熔断机制

如果命令连续失败 2 次：
1. **停止重试**
2. **记录到 notes.md**
3. **汇报用户** 并等待指示

---

## 📝 经验教训日志

| 日期 | 问题 | 原因 | 解决方案 |
|------|------|------|----------|
| 2026-01-23 | `mongosh: not found` | MongoDB 4.4 没有 mongosh | 改用 `mongo` 命令 |

