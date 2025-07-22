#!/bin/bash
# Claude Code 集成 - 快速测试脚本

echo "🧪 Claude Code 集成系统测试"
echo "============================"
echo ""

# 检查文件是否存在
echo "📁 检查文件..."
if [ -f "/Users/imac/Documents/编程/项目/本地llm项目/claude_simulator.py" ]; then
    echo "✅ claude_simulator.py 存在"
else
    echo "❌ claude_simulator.py 不存在"
fi

if [ -f "$HOME/.local/bin/claude" ]; then
    echo "✅ claude 命令已安装"
else
    echo "❌ claude 命令未安装"
fi

echo ""
echo "🚀 测试功能..."

# 测试创建项目
echo "1. 创建测试项目..."
python3 /Users/imac/Documents/编程/项目/本地llm项目/claude_simulator.py "create a test project" > /tmp/test_result.json
if [ $? -eq 0 ]; then
    echo "✅ 项目创建成功"
    cat /tmp/test_result.json | python3 -m json.tool
else
    echo "❌ 项目创建失败"
fi

echo ""
echo "📂 输出目录内容："
ls -la ~/claude-code-output/

echo ""
echo "✨ 测试完成！"
echo ""
echo "💡 使用方法："
echo "  1. 终端直接使用: claude 'create a project'"
echo "  2. 使用助手: ./claude_helper.sh create my-project"
echo "  3. 让Claude调用: 告诉我'用claude code创建项目'"
