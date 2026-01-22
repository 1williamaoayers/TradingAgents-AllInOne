---
description: 强制开工流程 (Action-Gated)
trigger_keywords: ["开始", "继续", "Start"]
---

# 🛑 强制开工检查

必须按顺序执行以下动作，**不可跳过**。

## 动作 1: 物理激活记忆 (Mandatory Write)
必须在 `notes.md` 写入启动日志，证明你已挂载记忆。

```powershell
Add-Content -Path "notes.md" -Value "`n## Session Start: [当前时间]`n- 记忆系统已激活。"
```

## 动作 2: 获取上下文 (Read)
1. `view_file .antigravityrules`
2. `view_file TODO.md` (关注顶部警告和当前任务)
3. `view_file notes.md` (关注最后一次 Handover)

## 动作 3: 同步检查 (Sync Check)
- 检查 `TODO.md` 的当前任务是否与 `notes.md` 的 Handover 一致？
- **如果不一致**：立即更新 `TODO.md`。
- **如果一致**：继续。

## 动作 4: 汇报 (Report)
向用户汇报："🚀 系统启动。记忆已挂载。当前任务：[xxx] (源自 TODO.md)"
