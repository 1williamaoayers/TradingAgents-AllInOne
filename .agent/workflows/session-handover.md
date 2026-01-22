---
description: 存档协议 - Session Handover Protocol
trigger_keywords: ["收工", "存档", "暂停", "下班"]
---

# 存档协议 - SESSION HANDOVER

## 触发条件
- 用户说"收工"、"暂停"、"下班"
- 任务阶段性完成

---

## 执行步骤

### 步骤1：更新 TODO.md
- 将已完成任务标记为 `[x]`
- 将进行中任务保持 `[ ]` 状态
- 添加关键警告（如果有）

### 步骤2：写入 notes.md
在文件末尾追加 SESSION HANDOVER：

```markdown
## SESSION HANDOVER - [当前时间]
- **进度**: [用大白话描述当前进度]
- **卡点**: [如果有报错或问题，详细记录]
- **下一步**: [告诉下一个 Agent 第一步该干什么]
- **关键文件**: [列出相关文件路径]
```

### 步骤3：汇报
"✅ 存档完毕。进度在 TODO.md，细节在 notes.md。下次说'继续'/‘开始’即可恢复。"

---

## 示例

### 好的存档示例
```markdown
## SESSION HANDOVER - 2024-01-22 18:30
- **进度**: 用户登录功能已完成 80%，API 接口已实现，前端页面还差表单验证
- **卡点**: 表单验证库版本冲突，需要升级 react-hook-form 到 v7
- **下一步**: 先运行 `npm install react-hook-form@latest`，然后修改 LoginForm.tsx
- **关键文件**: 
  - src/api/auth.ts (已完成)
  - src/components/LoginForm.tsx (进行中)
  - package.json (需要更新)
```
