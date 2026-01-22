---
name: Rule Watchdog
description: Scans recent conversation/actions for rule violations.
trigger_keywords: ["监控", "审查", "查违规", "Audit"]
---

# 🕵️ Rule Watchdog Skill

## 目标
主动审查最近的操作，寻找违规迹象。

## 触发条件
- 用户指令: "监控", "审查", "查违规"
- 定期自检 (建议每 10 个步骤触发一次)

## 执行步骤

### 步骤 1: 读取上下文
读取 `notes.md` 的最近 50 行，以及 `TODO.md`。

### 步骤 2: 审计逻辑 (Audit Logic)

对着以下清单逐条核对：

#### 1. 语言一致性
- [ ] 最近的回复是纯中文吗？
- [ ] `task.md` / `implementation_plan.md` 是纯中文吗？

#### 2. 记忆同步性
- [ ] `TODO.md` 的 Update Time 是否晚于 `notes.md`？
- [ ] 是否存在 "做了事但没改 TODO" 的情况？

#### 3. 证据链 (Evidence)
- [ ] `notes.md` 里有报错信息吗？
- [ ] 如果有报错，是否记录了修复方案？
- [ ] 如果标记了 `[x] Completed`，是否提供了 Verification Log？

### 步骤 3: 产出报告

如果发现问题，生成 **违规报告**：

```markdown
# 🚨 违规警报

1. **[违规项]**: 语言一致性
   - **详情**: 在 task.md 中发现了英文。
   - **建议**: 立即重写为中文。

2. **[违规项]**: 记忆同步性
   - **详情**: TODO.md 落后于实际进度。
   - **建议**: 立即执行 sync。
```

如果没有问题，汇报：
"✅ 看门狗审查完毕：一切正常。"
