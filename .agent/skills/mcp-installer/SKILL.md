---
name: MCP Installer
description: Automates the configuration of new MCP servers in Antigravity.
trigger_keywords: ["安装MCP", "Install MCP", "配置MCP", "Config MCP"]
---

# MCP Installer Skill

## 1. 目标
快速、准确地修改 Antigravity 的 `mcp_config.json` 文件，添加新的 MCP 服务器配置。

## 2. 核心路径
配置文件位于：`c:\Users\Administrator\.gemini\antigravity\mcp_config.json`

## 3. 执行步骤

### 步骤 1: 获取信息
确认用户想安装哪个 MCP，以及它的 `command` (如 `npx`) 和 `args` (如 `-y @package/name`)。

### 步骤 2: 读取配置
使用 `view_file` 读取当前的 `mcp_config.json`。

### 步骤 3: 注入配置
使用 `write_to_file` (覆盖) 或 `replace_file_content` (如果太长)，将新配置合并到 `mcpServers` 对象中。

**JSON 模板**:
```json
{
  "mcpServers": {
    "EXISTING_SERVERS": "...",
    "NEW_SERVER_NAME": {
      "command": "npx",
      "args": ["-y", "PACKAGE_NAME"]
    }
  }
}
```

### 步骤 4: 重启指引
修改完成后，必须告诉用户：
1. 回到 "Manage MCPs" 界面。
2. 点击右上角的 "Refresh" 按钮。

## 4. 示例
用户指令："帮我配一下 GitHub MCP"
操作：
1. 读取 config。
2. 注入 `{ "github": { ... } }`。
3. 提示刷新。
