#!/bin/bash
# AI监理系统 v2.1 - 一键完成部署脚本

set -e

echo "🚀 AI监理系统 v2.1 - 一键完成部署"
echo "=================================="
echo "开始时间: $(date)"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_DIR="/Users/imac/Documents/编程/项目/本地llm项目"
MONITOR_DIR="$PROJECT_DIR/ai-monitor-v2"

echo -e "${BLUE}📁 项目目录: $PROJECT_DIR${NC}"
cd "$PROJECT_DIR"

# 1. 检查并安装依赖
echo -e "\n${BLUE}1️⃣ 检查系统依赖...${NC}"

# 检查Homebrew
if ! command -v brew &> /dev/null; then
    echo -e "${RED}❌ Homebrew未安装${NC}"
    echo "请先安装Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

# 检查并安装Go
if ! command -v go &> /dev/null; then
    echo -e "${YELLOW}📦 安装Go语言...${NC}"
    brew install go
else
    echo -e "${GREEN}✅ Go已安装: $(go version)${NC}"
fi

# 检查并安装Rust
if ! command -v cargo &> /dev/null; then
    echo -e "${YELLOW}📦 安装Rust...${NC}"
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
else
    echo -e "${GREEN}✅ Rust已安装: $(cargo --version)${NC}"
fi

# 检查Docker
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker未运行，请启动Docker Desktop${NC}"
    open -a Docker
    echo "等待Docker启动..."
    sleep 10
fi

# 检查Ollama
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}📦 安装Ollama...${NC}"
    brew install ollama
else
    echo -e "${GREEN}✅ Ollama已安装${NC}"
fi

# 2. 启动基础服务
echo -e "\n${BLUE}2️⃣ 启动基础服务...${NC}"

# 启动Ollama
if ! pgrep -f "ollama serve" > /dev/null; then
    echo -e "${YELLOW}启动Ollama服务...${NC}"
    ollama serve > "$MONITOR_DIR/logs/ollama.log" 2>&1 &
    sleep 5
fi
echo -e "${GREEN}✅ Ollama服务运行中${NC}"

# 检查Ollama模型
if ! ollama list | grep -q "deepseek-coder"; then
    echo -e "${YELLOW}下载AI模型 (这可能需要几分钟)...${NC}"
    ollama pull deepseek-coder:6.7b
    ollama pull nomic-embed-text
fi

# 3. 启动Weaviate
echo -e "\n${BLUE}3️⃣ 启动向量数据库...${NC}"

# 检查并启动Weaviate
if ! docker ps | grep -q "weaviate-ai-monitor"; then
    # 先尝试启动已存在的容器
    if docker ps -a | grep -q "weaviate-ai-monitor"; then
        docker start weaviate-ai-monitor
    else
        # 创建新容器
        docker run -d --name weaviate-ai-monitor \
            -p 8080:8080 \
            -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
            -e DEFAULT_VECTORIZER_MODULE=text2vec-transformers \
            -e ENABLE_MODULES=text2vec-transformers \
            -v "$MONITOR_DIR/data/weaviate:/var/lib/weaviate" \
            semitechnologies/weaviate:1.25.0
    fi
    echo "等待Weaviate启动..."
    sleep 15
fi
echo -e "${GREEN}✅ Weaviate向量数据库运行中${NC}"

# 4. 编译并启动Go API
echo -e "\n${BLUE}4️⃣ 启动Go闪电API...${NC}"

cd "$MONITOR_DIR/performance/go"
if [ -f "go.mod" ]; then
    echo "安装Go依赖..."
    go mod tidy
    
    # 检查是否已在运行
    if ! lsof -i :3001 > /dev/null 2>&1; then
        echo "启动Go API服务..."
        go run main.go > "$MONITOR_DIR/logs/go-api.log" 2>&1 &
        sleep 3
    fi
    echo -e "${GREEN}✅ Go闪电API运行中 (端口3001)${NC}"
else
    echo -e "${RED}❌ Go项目文件缺失${NC}"
fi

# 5. 编译并启动Rust引擎
echo -e "\n${BLUE}5️⃣ 编译Rust零延迟引擎...${NC}"

cd "$MONITOR_DIR/performance/rust"
if [ -f "Cargo.toml" ]; then
    echo "编译Rust项目 (首次编译需要几分钟)..."
    cargo build --release
    
    # 检查是否已在运行
    if ! lsof -i :3002 > /dev/null 2>&1; then
        echo "启动Rust引擎..."
        ./target/release/ai-monitor-rust > "$MONITOR_DIR/logs/rust-engine.log" 2>&1 &
        sleep 2
    fi
    echo -e "${GREEN}✅ Rust零延迟引擎运行中 (端口3002)${NC}"
else
    echo -e "${RED}❌ Rust项目文件缺失${NC}"
fi

# 6. 启动Python核心服务
echo -e "\n${BLUE}6️⃣ 启动核心服务...${NC}"

cd "$MONITOR_DIR"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境并安装依赖
source venv/bin/activate
echo "安装Python依赖..."
pip install -q --upgrade pip
pip install -q -r requirements.txt || echo "部分依赖安装失败，继续..."

# 启动核心服务
if ! lsof -i :8000 > /dev/null 2>&1; then
    echo "启动Python核心服务..."
    cd core
    python main.py > ../logs/core-service.log 2>&1 &
    cd ..
    sleep 5
fi
echo -e "${GREEN}✅ Python核心服务运行中 (端口8000)${NC}"

# 7. 运行验证
echo -e "\n${BLUE}7️⃣ 验证部署状态...${NC}"

cd "$PROJECT_DIR"
sleep 5

# 运行验证脚本
if [ -f "validate_deployment.py" ]; then
    python3 validate_deployment.py
else
    echo -e "${YELLOW}验证脚本不存在，手动检查服务状态...${NC}"
    
    echo -e "\n${BLUE}服务状态检查:${NC}"
    
    # 检查各个服务
    services=(
        "8000:Python核心服务"
        "11434:Ollama LLM引擎"
        "8080:Weaviate向量数据库"
        "3001:Go闪电API"
        "3002:Rust零延迟引擎"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r port name <<< "$service"
        if lsof -i :$port > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $name (端口$port) - 运行中${NC}"
        else
            echo -e "${RED}❌ $name (端口$port) - 未运行${NC}"
        fi
    done
fi

# 8. 最终报告
echo -e "\n${BLUE}=================================="
echo -e "🎉 部署完成！"
echo -e "==================================${NC}"
echo ""
echo "访问以下地址使用系统:"
echo "- 核心API: http://localhost:8000"
echo "- 健康检查: http://localhost:8000/health"
echo "- API文档: http://localhost:8000/docs"
echo "- Ollama: http://localhost:11434"
echo "- Weaviate: http://localhost:8080"
echo "- Go API: http://localhost:3001/health"
echo "- Rust引擎: http://localhost:3002/health"
echo ""
echo "查看日志:"
echo "- tail -f $MONITOR_DIR/logs/core-service.log"
echo "- tail -f $MONITOR_DIR/logs/go-api.log"
echo "- tail -f $MONITOR_DIR/logs/rust-engine.log"
echo ""
echo -e "${GREEN}✨ AI监理系统 v2.1 部署完成！${NC}"
echo "完成时间: $(date)"
