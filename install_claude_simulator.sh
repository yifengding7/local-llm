#!/bin/bash
# 安装Claude Code模拟器

echo "🚀 安装Claude Code模拟器..."

# 创建本地bin目录
mkdir -p ~/.local/bin

# 复制模拟器脚本
cp claude_simulator.py ~/.local/bin/claude
chmod +x ~/.local/bin/claude

# 确保~/.local/bin在PATH中
if ! echo $PATH | grep -q "$HOME/.local/bin"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bash_profile
fi

# 创建一个别名方便调用
echo "alias claude-code='python3 ~/.local/bin/claude'" >> ~/.zshrc
echo "alias claude-code='python3 ~/.local/bin/claude'" >> ~/.bash_profile

echo "✅ Claude Code模拟器安装完成！"
echo ""
echo "使用方法:"
echo "  claude 'create a Python project named test-app'"
echo "  echo 'analyze this code' | claude"
echo ""
echo "请运行以下命令使更改生效:"
echo "  source ~/.zshrc"
echo "或重新打开终端"
