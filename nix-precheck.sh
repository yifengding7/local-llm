#!/usr/bin/env bash

# Nix环境部署预检查脚本
# 用于快速评估项目当前状态

echo "🔍 AI监理系统 - Nix部署预检查"
echo "================================"

# 1. 检查当前目录
echo -e "\n📁 当前目录检查:"
if [ "$(basename "$PWD")" = "本地llm项目" ]; then
    echo "✅ 在正确的项目目录"
else
    echo "❌ 请先cd到项目目录: /Users/imac/Documents/编程/项目/本地llm项目"
    exit 1
fi

# 2. 检查现有环境管理
echo -e "\n🔧 现有环境管理检查:"
[ -f "requirements.txt" ] && echo "✓ 发现 requirements.txt"
[ -f "pyproject.toml" ] && echo "✓ 发现 pyproject.toml (Poetry)"
[ -f "poetry.lock" ] && echo "✓ 发现 poetry.lock"
[ -f "package.json" ] && echo "✓ 发现 package.json (Node.js)"
[ -f "go.mod" ] && echo "✓ 发现 go.mod (Go)"
[ -f "Cargo.toml" ] && echo "✓ 发现 Cargo.toml (Rust)"
[ -f "docker-compose.yml" ] && echo "✓ 发现 docker-compose.yml"

# 3. 检查是否已有Nix配置
echo -e "\n📦 Nix配置检查:"
if [ -f "flake.nix" ]; then
    echo "⚠️  已存在 flake.nix - 将被覆盖"
    echo "   建议先备份: cp flake.nix flake.nix.backup"
fi
[ -f "shell.nix" ] && echo "⚠️  已存在 shell.nix"
[ -f ".envrc" ] && echo "⚠️  已存在 .envrc"

# 4. 检查系统工具
echo -e "\n🛠️  系统工具检查:"
command -v nix >/dev/null && echo "✓ Nix 已安装: $(nix --version)" || echo "✗ Nix 未安装"
command -v direnv >/dev/null && echo "✓ direnv 已安装" || echo "✗ direnv 未安装（可选）"
command -v git >/dev/null && echo "✓ Git 已安装" || echo "✗ Git 未安装"

# 5. 检查磁盘空间
echo -e "\n💾 磁盘空间检查:"
df -h . | grep -v Filesystem | awk '{print "可用空间: " $4 " (需要至少 5GB)"}'

# 6. 检查网络连接
echo -e "\n🌐 网络连接检查:"
if ping -c 1 github.com >/dev/null 2>&1; then
    echo "✅ GitHub 连接正常"
else
    echo "❌ 无法连接 GitHub"
fi

# 7. 生成依赖摘要
echo -e "\n📊 项目依赖摘要:"
if [ -f "requirements.txt" ]; then
    echo "Python 主要依赖:"
    head -10 requirements.txt | grep -v "^#" | grep -v "^$" | sed 's/^/  - /'
    total=$(grep -v "^#" requirements.txt | grep -v "^$" | wc -l)
    echo "  ... 总计 $total 个Python包"
fi

# 8. 建议
echo -e "\n💡 部署建议:"
echo "1. 首次部署预计需要 30-45 分钟"
echo "2. 建议先备份重要配置文件"
echo "3. 确保网络连接稳定"
echo "4. 可以使用 screen 或 tmux 避免中断"

echo -e "\n✅ 预检查完成！可以开始执行部署。"
