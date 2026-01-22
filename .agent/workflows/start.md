---
description: 强制开工流程 (Action-Gated)
trigger_keywords: ["开始", "继续", "Start"]
---

# 🛑 强制开工检查

必须按顺序执行以下动作，**不可跳过**。

## 动作 1: 物理激活记忆 (Mandatory Write)
必须在 `notes.md` 写入启动日志，证明你已挂载记忆。

**操作指南**: 请使用你的 **File Editing Tool** (如 `replace_file_content` 或 `write_to_file`) 在文件末尾追加以下内容。
**不要** 使用终端命令 (run_command)，以避免触发安全弹窗。

**写入内容模板**:
```markdown
## Session Start: [当前时间]
- 记忆系统已激活。
- [其他启动信息]
```

## 动作 2: 获取上下文 (Read)
1. `view_file .antigravityrules`
2. `view_file TODO.md` (关注顶部警告和当前任务)
3. `view_file notes.md` (关注最后一次 Handover)

## 动作 3: 同步检查 (Sync Check)
- 检查 `TODO.md` 的当前任务是否与 `notes.md` 的 Handover 一致？
- **如果不一致**：立即更新 `TODO.md`。
- **如果一致**：继续。

## 动作 4: 汇报与执行 (Report or Execute)

判断当前状态：
1. **静默模式 (Silent Mode)**：如果 `TODO.md` 中有明确的 `[ ] [P0]` 紧急任务，**不要**调用 `notify_user` 中断流程。直接开始执行任务！
2. **常规模式**：如果暂无明确任务，向用户汇报："🚀 系统启动。记忆已挂载..."
