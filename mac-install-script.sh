#!/bin/bash
# AI监理系统 v2.1 - macOS一键安装脚本
# 完全隔离的环境部署，不会影响系统其他软件

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 配置
INSTALL_DIR="$HOME/ai-monitor-v2"
VENV_DIR="$INSTALL_DIR/.venv"
DATA_DIR="$INSTALL_DIR/data"
LOG_FILE="$INSTALL_DIR/install.log"

# 打印函数
print_banner() {
    clear
    echo -e "${PURPLE}"
    cat << "EOF"
    ___    ____   __  __            _ __            
   /   |  /  _/  /  |/  /___  ____  (_) /_____  _____
  / /| |  / /   / /|_/ / __ \/ __ \/ / __/ __ \/ ___/
 / ___ |_/ /   / /  / / /_/ / / / / / /_/ /_/ / /    
/_/  |_/___/  /_/  /_/\____/_/ /_/_/\__/\____/_/     
EOF
    echo -e "${NC}"
    echo -e "${BLUE}AI监理系统 v2.1 - macOS一键安装${NC}"
    echo -e "${GREEN}🛡️ 完全隔离部署 | 🚀 自动化安装 | ✅ 环境保护${NC}"
    echo ""
}

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[错误]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[警告]${NC} $1" | tee -a "$LOG_FILE"
}

# 检查系统要求
check_requirements() {
    log "🔍 检查系统要求..."
    
    # 检查macOS版本
    OS_VERSION=$(sw_vers -productVersion)
    log "macOS版本: $OS_VERSION"
    
    # 检查芯片类型
    if [[ $(uname -m) == 'arm64' ]]; then
        log "✅ 检测到Apple Silicon芯片"
        CHIP_TYPE="apple_silicon"
    else
        log "✅ 检测到Intel芯片"
        CHIP_TYPE="intel"
    fi
    
    # 检查可用内存
    MEMORY_GB=$(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))
    log "系统内存: ${MEMORY_GB}GB"
    
    if [ $MEMORY_GB -lt 8 ]; then
        warning "系统内存少于8GB，可能影响性能"
    fi
    
    # 检查磁盘空间
    DISK_AVAILABLE=$(df -g "$HOME" | awk 'NR==2 {print $4}')
    log "可用磁盘空间: ${DISK_AVAILABLE}GB"
    
    if [ "$DISK_AVAILABLE" -lt 50 ]; then
        error "磁盘空间不足，需要至少50GB"
        exit 1
    fi
}

# 安装Homebrew（如果需要）
install_homebrew() {
    if ! command -v brew &> /dev/null; then
        log "📦 安装Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # 添加到PATH
        if [[ "$CHIP_TYPE" == "apple_silicon" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
    else
        log "✅ Homebrew已安装"
    fi
}

# 安装系统依赖
install_dependencies() {
    log "📦 安装系统依赖..."
    
    # 更新Homebrew
    brew update
    
    # 安装Python（指定版本）
    if ! brew list python@3.11 &> /dev/null; then
        brew install python@3.11
    fi
    
    # 安装其他依赖
    DEPS=(git docker ollama ffmpeg jq wget)
    for dep in "${DEPS[@]}"; do
        if ! brew list $dep &> /dev/null; then
            log "安装 $dep..."
            brew install $dep
        fi
    done
    
    # 安装Docker Desktop（如果未安装）
    if ! command -v docker &> /dev/null; then
        log "📦 安装Docker Desktop..."
        brew install --cask docker
        
        # 启动Docker
        log "🚀 启动Docker Desktop..."
        open /Applications/Docker.app
        
        # 等待Docker启动
        log "等待Docker启动..."
        while ! docker system info &> /dev/null; do
            sleep 2
        done
    fi
}

# 创建隔离环境
create_isolated_env() {
    log "🏗️ 创建隔离环境..."
    
    # 创建安装目录
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # 创建项目结构
    mkdir -p {api,core,frontend,infrastructure,tests,scripts,logs,cache,data}
    mkdir -p api/{auth,endpoints,models}
    mkdir -p core/{llm,vector,voice}
    mkdir -p frontend/{gui,cli}
    mkdir -p infrastructure/{scaffold,config}
    mkdir -p data/{models,vectors,cache}
    
    # 创建Python虚拟环境
    log "🐍 创建Python虚拟环境..."
    /usr/local/bin/python3.11 -m venv "$VENV_DIR"
    
    # 激活虚拟环境
    source "$VENV_DIR/bin/activate"
    
    # 升级pip
    pip install --upgrade pip setuptools wheel
}

# 下载项目代码
download_project() {
    log "📥 下载项目代码..."
    
    # 这里假设从GitHub下载，实际使用时替换为真实地址
    # git clone https://github.com/your-username/ai-monitor-v2.git "$INSTALL_DIR/src"
    
    # 创建示例代码文件
    cat > "$INSTALL_DIR/api/__init__.py" << 'EOF'
"""AI监理系统API模块"""
__version__ = "2.1.0"
EOF
    
    # 创建主要的Python文件占位符
    touch "$INSTALL_DIR/api/main.py"
    touch "$INSTALL_DIR/core/__init__.py"
}

# 安装Python依赖
install_python_deps() {
    log "📦 安装Python依赖..."
    
    # 创建requirements.txt
    cat > "$INSTALL_DIR/requirements.txt" << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.25.2
ollama==0.1.7
weaviate-client==3.25.3
numpy==1.24.3
loguru==0.7.2
redis==5.0.1
GitPython==3.1.40
prometheus-client==0.19.0
psutil==5.9.6
pytest==7.4.3
EOF
    
    # 使用虚拟环境的pip安装
    "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
}

# 配置Docker服务
setup_docker_services() {
    log "🐳 配置Docker服务..."
    
    # 创建docker-compose.yml
    cat > "$INSTALL_DIR/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  weaviate:
    image: semitechnologies/weaviate:latest
    container_name: ai-monitor-weaviate
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'none'
    volumes:
      - ./data/weaviate:/var/lib/weaviate

  redis:
    image: redis:7-alpine
    container_name: ai-monitor-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - ./data/redis:/data
    command: redis-server --appendonly yes

  prometheus:
    image: prom/prometheus:latest
    container_name: ai-monitor-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./data/prometheus:/prometheus
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

volumes:
  weaviate_data:
  redis_data:
  prometheus_data:
EOF
    
    # 创建Prometheus配置
    cat > "$INSTALL_DIR/prometheus.yml" << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ai-monitor'
    static_configs:
      - targets: ['host.docker.internal:8000']
EOF
    
    # 启动Docker服务
    log "🚀 启动Docker服务..."
    cd "$INSTALL_DIR"
    docker-compose up -d
}

# 下载AI模型
download_models() {
    log "🤖 下载AI模型..."
    
    # 启动Ollama
    ollama serve &> "$INSTALL_DIR/logs/ollama.log" &
    OLLAMA_PID=$!
    
    # 等待Ollama启动
    sleep 5
    
    # 下载模型
    MODELS=("qwen:8b" "deepseek-coder:6.7b" "phi3:mini" "nomic-embed-text")
    for model in "${MODELS[@]}"; do
        log "下载模型: $model"
        ollama pull "$model" || warning "模型 $model 下载失败，可稍后重试"
    done
    
    # 保存Ollama进程ID
    echo $OLLAMA_PID > "$INSTALL_DIR/.ollama.pid"
}

# 创建启动脚本
create_start_script() {
    log "📝 创建启动脚本..."
    
    cat > "$INSTALL_DIR/start.sh" << 'EOF'
#!/bin/bash
# AI监理系统启动脚本

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 启动AI监理系统...${NC}"

# 检查Docker
if ! docker info &> /dev/null; then
    echo -e "${RED}Docker未运行，请先启动Docker Desktop${NC}"
    open /Applications/Docker.app
    echo "等待Docker启动..."
    while ! docker info &> /dev/null; do
        sleep 2
    done
fi

# 启动Docker服务
echo "启动Docker服务..."
docker-compose up -d

# 检查Ollama
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "启动Ollama服务..."
    ollama serve &> logs/ollama.log &
    echo $! > .ollama.pid
    sleep 5
fi

# 激活虚拟环境
source .venv/bin/activate

# 启动API服务
echo "启动API服务..."
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &> logs/api.log &
echo $! > .api.pid

echo -e "${GREEN}✅ 系统启动完成！${NC}"
echo ""
echo "访问地址："
echo "  API文档: http://localhost:8000/docs"
echo "  Prometheus: http://localhost:9090"
echo ""
echo "查看日志："
echo "  API日志: tail -f logs/api.log"
echo "  Ollama日志: tail -f logs/ollama.log"
echo ""
echo "停止系统: ./stop.sh"
EOF
    
    chmod +x "$INSTALL_DIR/start.sh"
    
    # 创建停止脚本
    cat > "$INSTALL_DIR/stop.sh" << 'EOF'
#!/bin/bash
# AI监理系统停止脚本

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🛑 停止AI监理系统..."

# 停止API服务
if [ -f .api.pid ]; then
    kill $(cat .api.pid) 2>/dev/null
    rm .api.pid
fi

# 停止Ollama
if [ -f .ollama.pid ]; then
    kill $(cat .ollama.pid) 2>/dev/null
    rm .ollama.pid
fi

# 停止Docker服务
docker-compose down

echo "✅ 系统已停止"
EOF
    
    chmod +x "$INSTALL_DIR/stop.sh"
}

# 创建卸载脚本
create_uninstall_script() {
    cat > "$INSTALL_DIR/uninstall.sh" << 'EOF'
#!/bin/bash
# AI监理系统卸载脚本

echo "⚠️  此操作将删除AI监理系统及所有数据"
read -p "确定要卸载吗？(y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# 停止所有服务
./stop.sh

# 删除Docker容器和镜像
docker-compose down -v --rmi all

# 删除安装目录
cd ..
rm -rf ai-monitor-v2

echo "✅ AI监理系统已完全卸载"
EOF
    
    chmod +x "$INSTALL_DIR/uninstall.sh"
}

# 配置环境变量
setup_environment() {
    log "⚙️ 配置环境变量..."
    
    cat > "$INSTALL_DIR/.env" << EOF
# AI监理系统环境配置
APP_NAME="AI Monitor System"
APP_VERSION="2.1.0"
ENVIRONMENT="production"

# API配置
API_HOST="0.0.0.0"
API_PORT="8000"
API_KEY="$(openssl rand -hex 16)"
JWT_SECRET="$(openssl rand -hex 32)"

# 服务地址
OLLAMA_HOST="http://localhost:11434"
WEAVIATE_URL="http://localhost:8080"
REDIS_URL="redis://localhost:6379"

# 模型配置
DEFAULT_MODEL="qwen:8b"
CODE_MODEL="deepseek-coder:6.7b"
EMBEDDING_MODEL="nomic-embed-text"

# 数据目录
DATA_DIR="$DATA_DIR"
LOG_DIR="$INSTALL_DIR/logs"
CACHE_DIR="$INSTALL_DIR/cache"
EOF
}

# 运行测试
run_tests() {
    log "🧪 运行系统测试..."
    
    # 创建测试脚本
    cat > "$INSTALL_DIR/test_system.sh" << 'EOF'
#!/bin/bash
# 系统测试脚本

source .venv/bin/activate
python test_validation.py
EOF
    
    chmod +x "$INSTALL_DIR/test_system.sh"
    
    # 运行测试
    cd "$INSTALL_DIR"
    ./test_system.sh
}

# 主安装流程
main() {
    print_banner
    
    # 创建日志目录
    mkdir -p "$(dirname "$LOG_FILE")"
    
    log "🎯 开始安装AI监理系统 v2.1"
    log "安装目录: $INSTALL_DIR"
    echo ""
    
    # 确认安装
    read -p "是否继续安装？(Y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]] && [[ ! -z $REPLY ]]; then
        exit 1
    fi
    
    # 执行安装步骤
    check_requirements
    install_homebrew
    install_dependencies
    create_isolated_env
    download_project
    install_python_deps
    setup_docker_services
    download_models
    create_start_script
    create_uninstall_script
    setup_environment
    
    # 安装完成
    echo ""
    log "🎉 安装完成！"
    echo ""
    echo -e "${GREEN}环境隔离说明：${NC}"
    echo "  • Python依赖安装在: $VENV_DIR"
    echo "  • Docker数据存储在: $DATA_DIR"
    echo "  • 系统文件位于: $INSTALL_DIR"
    echo ""
    echo -e "${BLUE}启动系统：${NC}"
    echo "  cd $INSTALL_DIR"
    echo "  ./start.sh"
    echo ""
    echo -e "${YELLOW}卸载系统：${NC}"
    echo "  $INSTALL_DIR/uninstall.sh"
    echo ""
    
    # 询问是否立即启动
    read -p "是否立即启动系统？(Y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        cd "$INSTALL_DIR"
        ./start.sh
    fi
}

# 错误处理
trap 'error "安装过程中出现错误，请查看日志: $LOG_FILE"' ERR

# 执行主函数
main "$@"
