#!/bin/bash
# 使用Claude Code配置整个LLM项目系统

echo "🤖 使用Claude Code自动配置系统..."
echo "================================"
echo ""

PROJECT_DIR="/Users/imac/Documents/编程/项目/本地llm项目"
cd "$PROJECT_DIR"

# 1. 创建系统配置文件
echo "📝 创建系统配置文件..."
cat > system_config.json << 'EOF'
{
  "project_name": "本地LLM项目",
  "version": "2.1.0",
  "services": {
    "ai_monitor": {
      "name": "AI监理系统",
      "enabled": true,
      "components": {
        "python_core": {
          "port": 8000,
          "start_cmd": "cd ai-monitor-v2/core && python3 main.py",
          "health_check": "http://localhost:8000/health"
        },
        "ollama": {
          "port": 11434,
          "start_cmd": "ollama serve",
          "models": ["deepseek-coder:6.7b", "nomic-embed-text", "phi3:mini"]
        },
        "weaviate": {
          "port": 8080,
          "start_cmd": "docker run -d --name weaviate-ai-monitor -p 8080:8080 semitechnologies/weaviate:1.25.0"
        }
      }
    },
    "claude_code": {
      "name": "Claude Code集成系统",
      "enabled": true,
      "components": {
        "simulator": {
          "path": "~/.local/bin/claude",
          "output_dir": "~/claude-code-output"
        }
      }
    },
    "performance": {
      "name": "性能加速系统",
      "enabled": true,
      "components": {
        "go_api": {
          "port": 3001,
          "start_cmd": "cd ai-monitor-v2/performance/go && go run main.go"
        },
        "rust_engine": {
          "port": 3002,
          "start_cmd": "cd ai-monitor-v2/performance/rust && cargo run --release"
        }
      }
    }
  },
  "environment": {
    "MOJO_ENABLE_NEURAL_ENGINE": "1",
    "METAL_DEVICE_WRAPPER_TYPE": "1",
    "GOMAXPROCS": "12",
    "RAYON_NUM_THREADS": "12",
    "PYTHONUNBUFFERED": "1"
  }
}
EOF

# 2. 创建自动启动脚本
echo "🚀 创建自动启动脚本..."
cat > auto_start.sh << 'EOF'
#!/bin/bash
# LLM项目自动启动脚本

source ~/.zshrc

echo "🚀 启动LLM项目所有服务..."
echo "========================"

# 设置环境变量
export MOJO_ENABLE_NEURAL_ENGINE=1
export METAL_DEVICE_WRAPPER_TYPE=1
export GOMAXPROCS=12
export RAYON_NUM_THREADS=12
export PYTHONUNBUFFERED=1

# 启动函数
start_service() {
    local name=$1
    local cmd=$2
    local port=$3
    
    echo "启动 $name..."
    
    # 检查端口是否已占用
    if [ ! -z "$port" ] && lsof -i :$port > /dev/null 2>&1; then
        echo "⚠️  $name 已在运行 (端口 $port)"
    else
        eval "$cmd > logs/${name}.log 2>&1 &"
        echo "✅ $name 启动成功"
    fi
}

# 创建日志目录
mkdir -p logs

# 启动Ollama
start_service "Ollama" "ollama serve" 11434

# 等待Ollama启动
sleep 5

# 下载必要的模型
echo "📥 检查AI模型..."
models=("deepseek-coder:6.7b" "nomic-embed-text" "phi3:mini")
for model in "${models[@]}"; do
    if ! ollama list | grep -q "$model"; then
        echo "下载模型: $model"
        ollama pull $model
    fi
done

# 启动Docker服务
if ! docker ps | grep -q "weaviate-ai-monitor"; then
    echo "启动Weaviate向量数据库..."
    docker run -d --name weaviate-ai-monitor \
        -p 8080:8080 \
        -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
        -e DEFAULT_VECTORIZER_MODULE=text2vec-transformers \
        -e ENABLE_MODULES=text2vec-transformers \
        -v "$(pwd)/data/weaviate:/var/lib/weaviate" \
        semitechnologies/weaviate:1.25.0
fi

# 启动Python核心服务
cd ai-monitor-v2
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "创建Python虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

start_service "Python核心服务" "cd core && python3 main.py" 8000

# 启动Go API (如果安装了Go)
if command -v go &> /dev/null; then
    start_service "Go API" "cd performance/go && go run main.go" 3001
fi

# 启动Rust引擎 (如果安装了Rust)
if command -v cargo &> /dev/null; then
    if [ ! -f "performance/rust/target/release/ai-monitor-rust" ]; then
        echo "编译Rust引擎..."
        cd performance/rust && cargo build --release && cd ../..
    fi
    start_service "Rust引擎" "cd performance/rust && ./target/release/ai-monitor-rust" 3002
fi

cd ..

echo ""
echo "✅ 所有服务启动完成！"
echo ""
echo "🌐 服务地址："
echo "  - 核心API: http://localhost:8000"
echo "  - API文档: http://localhost:8000/docs"
echo "  - Ollama: http://localhost:11434"
echo "  - Weaviate: http://localhost:8080"
echo "  - Go API: http://localhost:3001"
echo "  - Rust引擎: http://localhost:3002"
echo ""
echo "📊 控制面板: 运行 ./open_control.sh"
echo "📋 查看日志: tail -f logs/*.log"
echo "🛑 停止服务: ./auto_stop.sh"
EOF

chmod +x auto_start.sh

# 3. 创建自动停止脚本
echo "🛑 创建自动停止脚本..."
cat > auto_stop.sh << 'EOF'
#!/bin/bash
# LLM项目自动停止脚本

echo "🛑 停止LLM项目所有服务..."
echo "========================"

# 停止进程
pkill -f "ollama serve"
pkill -f "python.*8000"
pkill -f "go.*3001"
pkill -f "ai-monitor-rust"

# 停止Docker容器
docker stop weaviate-ai-monitor 2>/dev/null
docker rm weaviate-ai-monitor 2>/dev/null

echo "✅ 所有服务已停止"
EOF

chmod +x auto_stop.sh

# 4. 创建依赖安装脚本
echo "📦 创建依赖安装脚本..."
cat > install_dependencies.sh << 'EOF'
#!/bin/bash
# 安装所有依赖

echo "📦 安装LLM项目依赖..."
echo "===================="

# 检查Homebrew
if ! command -v brew &> /dev/null; then
    echo "安装Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# 安装系统依赖
echo "安装系统依赖..."
brew install python@3.11 ollama docker go rust

# 安装Python依赖
echo "安装Python依赖..."
cd ai-monitor-v2
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# 安装Go依赖
if [ -d "ai-monitor-v2/performance/go" ]; then
    echo "安装Go依赖..."
    cd ai-monitor-v2/performance/go
    go mod tidy
    cd ../..
fi

# 编译Rust项目
if [ -d "ai-monitor-v2/performance/rust" ]; then
    echo "编译Rust项目..."
    cd ai-monitor-v2/performance/rust
    cargo build --release
    cd ../..
fi

# 安装Claude Code模拟器
echo "安装Claude Code..."
./install_claude_simulator.sh

echo "✅ 所有依赖安装完成！"
EOF

chmod +x install_dependencies.sh

# 5. 创建健康检查脚本
echo "🏥 创建健康检查脚本..."
cat > health_check_all.sh << 'EOF'
#!/bin/bash
# 系统健康检查

echo "🏥 LLM项目健康检查"
echo "=================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

# 检查服务函数
check_service() {
    local name=$1
    local port=$2
    local url=$3
    
    if [ ! -z "$port" ]; then
        if lsof -i :$port > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $name (端口 $port) - 运行中${NC}"
            
            # 如果有健康检查URL，进行HTTP检查
            if [ ! -z "$url" ]; then
                if curl -s "$url" > /dev/null; then
                    echo -e "   ${GREEN}健康检查通过${NC}"
                else
                    echo -e "   ${YELLOW}健康检查失败${NC}"
                fi
            fi
        else
            echo -e "${RED}❌ $name (端口 $port) - 未运行${NC}"
        fi
    fi
}

# 检查进程
check_process() {
    local name=$1
    local process=$2
    
    if pgrep -f "$process" > /dev/null; then
        echo -e "${GREEN}✅ $name - 运行中${NC}"
    else
        echo -e "${RED}❌ $name - 未运行${NC}"
    fi
}

echo "📊 服务状态："
echo "-------------"
check_service "Python核心服务" 8000 "http://localhost:8000/health"
check_service "Ollama LLM" 11434 "http://localhost:11434/api/tags"
check_service "Weaviate向量库" 8080 "http://localhost:8080/v1/meta"
check_service "Go API" 3001 "http://localhost:3001/health"
check_service "Rust引擎" 3002 "http://localhost:3002/health"

echo ""
echo "📊 进程状态："
echo "-------------"
check_process "Ollama服务" "ollama serve"
check_process "Docker" "Docker"

echo ""
echo "💻 系统资源："
echo "-------------"
echo "CPU使用: $(top -l 1 | grep "CPU usage" | awk '{print $3}')"
echo "内存使用: $(top -l 1 | grep PhysMem | awk '{print $2, $4}')"
disk_usage=$(df -h / | awk 'NR==2 {print $5}')
echo "磁盘使用: $disk_usage"

echo ""
echo "📁 日志文件："
echo "-------------"
if [ -d "logs" ]; then
    ls -lh logs/*.log 2>/dev/null | tail -5
else
    echo "日志目录不存在"
fi

echo ""
echo "✅ 健康检查完成"
EOF

chmod +x health_check_all.sh

# 6. 创建一键配置脚本
echo "🎯 创建一键配置脚本..."
cat > setup_all.sh << 'EOF'
#!/bin/bash
# 一键配置整个系统

echo "🎯 LLM项目一键配置"
echo "=================="
echo ""

# 1. 安装依赖
echo "步骤 1/4: 安装依赖..."
./install_dependencies.sh

# 2. 创建必要目录
echo ""
echo "步骤 2/4: 创建目录结构..."
mkdir -p logs
mkdir -p data/weaviate
mkdir -p ~/claude-code-output
mkdir -p .pids

# 3. 配置环境变量
echo ""
echo "步骤 3/4: 配置环境变量..."
if ! grep -q "LLM_PROJECT_HOME" ~/.zshrc; then
    echo "export LLM_PROJECT_HOME=\"$(pwd)\"" >> ~/.zshrc
    echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> ~/.zshrc
    source ~/.zshrc
fi

# 4. 创建快捷命令
echo ""
echo "步骤 4/4: 创建快捷命令..."
cat > ~/.local/bin/llm << 'EOFCMD'
#!/bin/bash
# LLM项目快捷命令

case "$1" in
    start)
        cd "$LLM_PROJECT_HOME" && ./auto_start.sh
        ;;
    stop)
        cd "$LLM_PROJECT_HOME" && ./auto_stop.sh
        ;;
    status)
        cd "$LLM_PROJECT_HOME" && ./health_check_all.sh
        ;;
    ui)
        cd "$LLM_PROJECT_HOME" && ./open_control.sh
        ;;
    logs)
        cd "$LLM_PROJECT_HOME" && tail -f logs/*.log
        ;;
    *)
        echo "用法: llm {start|stop|status|ui|logs}"
        ;;
esac
EOFCMD

chmod +x ~/.local/bin/llm

# 5. 创建桌面快捷方式
./create_desktop_shortcut.sh

echo ""
echo "✅ 系统配置完成！"
echo ""
echo "🎉 快速使用指南："
echo "  llm start  - 启动所有服务"
echo "  llm stop   - 停止所有服务"
echo "  llm status - 查看服务状态"
echo "  llm ui     - 打开控制面板"
echo "  llm logs   - 查看日志"
echo ""
echo "或使用："
echo "  ./auto_start.sh    - 启动服务"
echo "  ./open_control.sh  - 打开UI"
echo ""
echo "享受您的AI之旅！🚀"
EOF

chmod +x setup_all.sh

echo ""
echo "✅ Claude Code 配置完成！"
echo ""
echo "已创建以下配置文件："
echo "  📄 system_config.json     - 系统配置"
echo "  🚀 auto_start.sh         - 自动启动脚本"
echo "  🛑 auto_stop.sh          - 自动停止脚本"
echo "  📦 install_dependencies.sh - 依赖安装"
echo "  🏥 health_check_all.sh    - 健康检查"
echo "  🎯 setup_all.sh          - 一键配置"
echo ""
echo "🎉 现在运行: ./setup_all.sh 完成配置"
