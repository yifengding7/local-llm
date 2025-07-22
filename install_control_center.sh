#!/bin/bash
# 安装控制中心

echo "🚀 安装本地LLM项目控制中心..."

# 设置执行权限
chmod +x control_center.sh
chmod +x claude_helper.sh
chmod +x complete_deployment.sh
chmod +x install_claude_simulator.sh
chmod +x test_claude_integration.sh

# 创建必要的目录
mkdir -p ~/.local/bin
mkdir -p ~/claude-code-output
mkdir -p .pids

# 创建快捷命令
echo '#!/bin/bash
cd /Users/imac/Documents/编程/项目/本地llm项目 && ./control_center.sh' > ~/.local/bin/llm-control
chmod +x ~/.local/bin/llm-control

# 添加到PATH（如果还没有）
if ! echo $PATH | grep -q "$HOME/.local/bin"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bash_profile
fi

# 创建桌面快捷方式（可选）
if [ -d ~/Desktop ]; then
    echo '#!/bin/bash
    osascript -e "tell application \"Terminal\" to do script \"llm-control\""' > ~/Desktop/LLM控制中心.command
    chmod +x ~/Desktop/LLM控制中心.command
fi

echo "✅ 安装完成！"
echo ""
echo "使用方法："
echo "1. 在终端输入: llm-control"
echo "2. 或运行: ./control_center.sh"
echo "3. 或双击桌面的'LLM控制中心.command'"
echo ""
echo "请运行 'source ~/.zshrc' 使快捷命令生效"
