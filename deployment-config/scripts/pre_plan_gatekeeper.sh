#!/bin/bash
# 预执行计划守门员脚本
# 在Claude CLI工具执行前运行

set -e

echo "🛡️ 预执行计划守门员检查..."

# 检查当前工作目录
current_dir=$(pwd)
echo "📍 当前目录: $current_dir"

# 检查是否在AI监理项目目录中
if [[ "$current_dir" == *"本地llm项目"* ]]; then
    echo "✅ 在AI监理项目目录中"
    
    # 检查关键配置文件
    if [[ -f "deployment-config/ai-monitor-v2.1-deployment.yaml" ]]; then
        echo "✅ 部署配置文件存在"
    else
        echo "⚠️  部署配置文件不存在"
    fi
    
    # 检查架构合规性
    if [[ -f "deployment-config/architecture-compliance.yaml" ]]; then
        echo "✅ 架构合规配置存在"
    else
        echo "⚠️  架构合规配置不存在"
    fi
    
else
    echo "ℹ️  不在AI监理项目目录中，跳过项目检查"
fi

# 检查系统资源
echo "💻 系统资源检查..."
memory_usage=$(ps -A -o %mem | awk '{s+=$1} END {print s "%"}')
echo "📊 内存使用率: $memory_usage"

# 检查关键服务状态
echo "🔍 检查关键服务..."
if pgrep -f "ollama" > /dev/null; then
    echo "✅ Ollama服务运行中"
else
    echo "⚠️  Ollama服务未运行"
fi

echo "✅ 预执行检查完成"
exit 0