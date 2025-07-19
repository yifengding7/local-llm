#!/bin/bash
# 通知处理脚本
# 重要变更实时提醒

set -e

echo "📢 通知处理器启动..."

# 检查是否有重要变更
if git rev-parse --git-dir > /dev/null 2>&1; then
    # 检查是否有未提交的更改
    if ! git diff --quiet || ! git diff --cached --quiet; then
        echo "🔔 检测到代码变更"
        
        # 获取更改统计
        changes=$(git diff --stat || echo "")
        staged_changes=$(git diff --cached --stat || echo "")
        
        if [ -n "$changes" ] || [ -n "$staged_changes" ]; then
            echo "📊 变更统计:"
            [ -n "$changes" ] && echo "工作区: $changes"
            [ -n "$staged_changes" ] && echo "暂存区: $staged_changes"
        fi
        
        # 检查是否有重要文件变更
        important_files=$(git diff --name-only HEAD 2>/dev/null | grep -E '\.(yaml|yml|json|py|js|ts|md)$' || true)
        if [ -n "$important_files" ]; then
            echo "⚠️  重要文件变更:"
            echo "$important_files"
        fi
        
        # 检查是否有配置文件变更
        config_files=$(git diff --name-only HEAD 2>/dev/null | grep -E '(config|settings|deployment)' || true)
        if [ -n "$config_files" ]; then
            echo "🔧 配置文件变更:"
            echo "$config_files"
            echo "💡 建议: 配置变更后请运行验证测试"
        fi
        
        # 检查是否有安全相关变更
        security_files=$(git diff --name-only HEAD 2>/dev/null | grep -E '(auth|security|permission|key)' || true)
        if [ -n "$security_files" ]; then
            echo "🔐 安全相关变更:"
            echo "$security_files"
            echo "⚠️  警告: 安全相关变更需要特别注意"
        fi
    else
        echo "✅ 没有待处理的变更"
    fi
else
    echo "ℹ️  不在git仓库中，跳过变更检测"
fi

# 检查系统资源状态
echo "💻 系统资源状态:"
memory_usage=$(ps -A -o %mem | awk '{s+=$1} END {print s}')
if (( $(echo "$memory_usage > 80" | bc -l) )); then
    echo "⚠️  内存使用率较高: ${memory_usage}%"
fi

# 检查是否有长时间运行的进程
long_running=$(ps -eo pid,etime,comm | awk 'NR>1 && $2 ~ /^[0-9]+-/ {print $3}' | sort | uniq -c | sort -nr | head -3)
if [ -n "$long_running" ]; then
    echo "🕒 长时间运行的进程:"
    echo "$long_running"
fi

# 检查AI监理系统相关服务
echo "🤖 AI监理系统服务状态:"
if pgrep -f "ollama" > /dev/null; then
    echo "✅ Ollama服务正常"
else
    echo "⚠️  Ollama服务未运行"
fi

if pgrep -f "redis" > /dev/null; then
    echo "✅ Redis服务正常"
else
    echo "ℹ️  Redis服务未运行"
fi

# 检查部署配置文件
if [ -f "deployment-config/ai-monitor-v2.1-deployment.yaml" ]; then
    echo "✅ 部署配置文件存在"
else
    echo "⚠️  部署配置文件缺失"
fi

# 生成通知摘要
echo "📋 通知摘要:"
echo "- 时间: $(date)"
echo "- 项目: AI监理系统 v2.1"
echo "- 状态: 监控中"

# 如果有重要变更，可以发送通知（可选）
# 这里可以集成Slack、邮件或其他通知系统
# 示例：
# if [ -n "$important_files" ]; then
#     curl -X POST -H 'Content-type: application/json' \
#         --data '{"text":"AI监理系统有重要变更"}' \
#         YOUR_SLACK_WEBHOOK_URL
# fi

echo "✅ 通知处理完成"
exit 0