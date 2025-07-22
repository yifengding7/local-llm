#!/bin/bash
# AI监理系统v2.1服务停止脚本

set -e

echo "🛑 停止AI监理系统v2.1服务..."
echo "📅 停止时间: $(date)"
echo ""

# 停止核心服务
echo "🐍 停止Python核心服务..."
pkill -f "python3.*8000" || echo "  - 核心服务已停止"

# 停止Go API服务
echo "⚡ 停止Go闪电API..."
pkill -f "go run main.go" || echo "  - Go API已停止"
pkill -f "go-lightning-api" || echo "  - Go API进程已停止"

# 停止Rust引擎
echo "🦀 停止Rust零延迟引擎..."
pkill -f "zero-delay-engine" || echo "  - Rust引擎已停止"

# 停止Weaviate服务
echo "🗂️ 停止Weaviate服务..."
if docker ps | grep -q "weaviate-ai-monitor"; then
    docker stop weaviate-ai-monitor
    docker rm weaviate-ai-monitor
    echo "  - Weaviate服务已停止"
else
    echo "  - Weaviate服务未运行"
fi

# 停止Ollama服务（可选）
echo "🦙 停止Ollama服务..."
read -p "是否要停止Ollama服务? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pkill -f "ollama serve" || echo "  - Ollama服务已停止"
else
    echo "  - 保持Ollama服务运行"
fi

# 清理日志（可选）
echo "🧹 清理日志文件..."
read -p "是否要清理日志文件? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -f logs/*.log
    echo "  - 日志文件已清理"
else
    echo "  - 保留日志文件"
fi

# 显示剩余进程
echo ""
echo "🔍 检查剩余进程..."
if pgrep -f "ollama" > /dev/null; then
    echo "  - Ollama进程仍在运行"
fi

if pgrep -f "python3.*8000" > /dev/null; then
    echo "  - Python核心服务仍在运行"
fi

if pgrep -f "go.*main.go" > /dev/null; then
    echo "  - Go API仍在运行"
fi

if docker ps | grep -q "weaviate"; then
    echo "  - Weaviate容器仍在运行"
fi

echo ""
echo "✅ AI监理系统v2.1服务停止完成！"
echo ""
echo "💡 提示:"
echo "  - 重新启动: ./start_services.sh"
echo "  - 检查状态: docker ps"
echo "  - 查看进程: ps aux | grep -E '(ollama|python3|go)'"