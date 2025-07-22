#!/usr/bin/env bash
set -e

# 安装或更新 MCP filesystem & github 服务器
npm i -g @modelcontextprotocol/server-filesystem@latest @modelcontextprotocol/server-github@latest

echo "✅ MCP servers installed."

echo "示例 Cursor MCP 配置 (~/.cursor/mcp.json)："
cat <<EOF
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "$(pwd)"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "ghp_***" }
    }
  }
}
EOF 