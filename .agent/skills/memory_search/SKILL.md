---
name: memory_search
description: Retrieve context from the project's long-term memory (m.py) before starting tasks.
---

# Memory Search Skill

## 🎯 目的 (Purpose)
Ensure every task benefits from the "long-term memory" of the project by retrieving API definitions (`概要.md`) and past experiences (`notes.md`) from `memory.db` before execution.

## 🔫 触发条件 (Trigger)
**MUST** be used before:
- Writing or modifying code.
- Using a specific API or library.
- Dealing with specific entities (e.g., stock codes like `01810`).
- Analyzing complex problems.

## 🎬 执行动作 (Action)
Run the following command in the project root:
```bash
python3 m.py search "[keyword]"
```
*(Replace `[keyword]` with the most relevant proper noun, ID, or error code)*

## 🧠 上下文分析 (Context Analysis)
After searching, you **MUST** read the output:
1.  **If API Docs appear**: Follow the parameter definitions strictly.
2.  **If "Success Stories" appear**: Replicate the proven logic.
3.  **If "Failure Logs" appear**: Explicitly avoid the recorded pitfalls.
