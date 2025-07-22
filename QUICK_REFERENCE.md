# 🎯 本地LLM项目 - 快速命令参考

## 🚀 控制中心启动

```bash
# 推荐方式 - 全局命令
llm-control

# 本地运行
cd /Users/imac/Documents/编程/项目/本地llm项目
./control_center.sh

# 桌面快捷方式
双击 ~/Desktop/LLM控制中心.command
```

## 📋 控制中心菜单快捷键

- `1` - 启动所有服务
- `2` - 停止所有服务  
- `3` - 查看服务状态
- `4` - Claude Code功能
- `5` - 查看日志
- `6` - 高级功能
- `7` - 查看文档
- `8` - 重启所有服务
- `0` - 退出

## 🤖 Claude Code快速命令

```bash
# 创建项目
claude "create a Python FastAPI project named my-api"
claude "create a React app with TypeScript"

# 分析代码
claude "analyze the security of /path/to/code.py"
claude "find bugs in main.js"

# 写代码
claude "write a function to sort a list"
claude "create a REST API endpoint for user authentication"

# 批量操作
./claude_helper.sh batch refactor "*.py"
./claude_helper.sh batch analyze "/project/*.js"
```

## 🛠️ 常用管理命令

```bash
# 健康检查
python3 health_check.py

# 系统诊断
python3 diagnose.py

# 查看日志
tail -f ai-monitor-v2/logs/core-service.log
tail -f ai-monitor-v2/logs/ollama.log

# 测试API
curl http://localhost:8000/health
curl http://localhost:11434/api/tags

# 查看端口占用
lsof -i :8000   # Python核心
lsof -i :11434  # Ollama
lsof -i :8080   # Weaviate
lsof -i :3001   # Go API
lsof -i :3002   # Rust引擎
```

## 🔧 服务管理

```bash
# 单独启动服务
ollama serve                          # Ollama
python3 ai-monitor-v2/core/main.py    # Python核心
docker start weaviate-ai-monitor      # Weaviate

# 停止特定服务
pkill -f "ollama serve"
pkill -f "python.*8000"
docker stop weaviate-ai-monitor

# 查看运行中的服务
ps aux | grep -E "(ollama|python|weaviate|go|rust)"
```

## 📁 重要目录

```bash
# 项目主目录
cd /Users/imac/Documents/编程/项目/本地llm项目

# AI监理系统
cd ai-monitor-v2/

# 日志目录
cd ai-monitor-v2/logs/

# Claude输出
cd ~/claude-code-output/

# 查看最新输出
ls -lat ~/claude-code-output/
```

## 🚨 故障排除

```bash
# 端口被占用
lsof -i :端口号
kill -9 进程ID

# 清理所有服务
./control_center.sh  # 选择2停止所有服务

# 重置环境
rm -rf .pids/
mkdir .pids/

# 更新依赖
cd ai-monitor-v2
source venv/bin/activate
pip install -r requirements.txt

# Docker问题
docker ps -a
docker rm -f $(docker ps -aq)
docker system prune
```

## ⚡ 性能优化

```bash
# 只启动基础服务
./control_center.sh  # 然后手动选择需要的服务

# 查看资源使用
top
htop  # 如果已安装

# 清理日志
rm -f ai-monitor-v2/logs/*.log

# 清理输出
rm -rf ~/claude-code-output/*
```

## 🔗 快速链接

- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health
- Ollama模型: http://localhost:11434/api/tags
- Weaviate控制台: http://localhost:8080/v1/meta

---

💡 **提示**: 将此文件保存或打印作为快速参考！

📝 **注意**: 所有路径基于 `/Users/imac/Documents/编程/项目/本地llm项目/`
