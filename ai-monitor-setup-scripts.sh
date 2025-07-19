#!/bin/bash
# setup.sh - AI监理系统 v2.1 安装和启动脚本

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# ASCII艺术标题
print_banner() {
    cat << "EOF"
    ___    ____   __  __            _ __            
   /   |  /  _/  /  |/  /___  ____  (_) /_____  _____
  / /| |  / /   / /|_/ / __ \/ __ \/ / __/ __ \/ ___/
 / ___ |_/ /   / /  / / /_/ / / / / / /_/ /_/ / /    
/_/  |_/___/  /_/  /_/\____/_/ /_/_/\__/\____/_/     
                                                      
        AI监理系统 v2.1 - Apple M3 Max优化版
        🚀 极致性能 | 🔥 零延迟 | 🤖 智能监理
EOF
    echo ""
}

# 检查系统要求
check_requirements() {
    print_info "检查系统要求..."
    
    # 检查操作系统
    if [[ "$OSTYPE" == "darwin"* ]]; then
        print_success "检测到 macOS 系统"
        
        # 检查是否为Apple Silicon
        if [[ $(uname -m) == 'arm64' ]]; then
            print_success "检测到 Apple Silicon (M3 Max)"
        else
            print_warning "未检测到 Apple Silicon，性能可能受限"
        fi
    else
        print_warning "非 macOS 系统，某些优化可能不可用"
    fi
    
    # 检查Python版本
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        if (( $(echo "$PYTHON_VERSION >= 3.9" | bc -l) )); then
            print_success "Python $PYTHON_VERSION ✓"
        else
            print_error "需要 Python 3.9 或更高版本"
            exit 1
        fi
    else
        print_error "未找到 Python3"
        exit 1
    fi
    
    # 检查Docker
    if command -v docker &> /dev/null; then
        print_success "Docker 已安装 ✓"
    else
        print_error "需要安装 Docker"
        exit 1
    fi
    
    # 检查Git
    if command -v git &> /dev/null; then
        print_success "Git 已安装 ✓"
    else
        print_error "需要安装 Git"
        exit 1
    fi
}

# 创建项目结构
create_project_structure() {
    print_info "创建项目结构..."
    
    # 创建目录
    directories=(
        "api/auth"
        "api/endpoints"
        "api/models"
        "core/llm"
        "core/vector"
        "core/voice"
        "frontend/gui/components"
        "frontend/cli/commands"
        "infrastructure/scaffold/templates"
        "infrastructure/scaffold/rules"
        "infrastructure/logging"
        "infrastructure/config"
        "mcp/filesystem"
        "mcp/github"
        "performance/mojo"
        "performance/rust/src"
        "performance/go"
        "tests/unit"
        "tests/integration"
        "scripts"
        "docs"
        "docker/services"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        touch "$dir/__init__.py" 2>/dev/null || true
    done
    
    print_success "项目结构创建完成"
}

# 安装Python依赖
install_python_deps() {
    print_info "安装Python依赖..."
    
    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "虚拟环境创建完成"
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 创建requirements.txt
    cat > requirements.txt << EOF
# Core dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# AI/ML dependencies
ollama==0.1.7
weaviate-client==3.25.3
numpy==1.24.3
tiktoken==0.5.1

# Utilities
loguru==0.7.2
click==8.1.7
rich==13.7.0
httpx==0.25.2
aiofiles==23.2.1

# Development
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
ruff==0.1.6

# Git integration
GitPython==3.1.40

# Performance monitoring
prometheus-client==0.19.0
psutil==5.9.6
EOF
    
    # 安装依赖
    pip install -r requirements.txt
    
    print_success "Python依赖安装完成"
}

# 下载AI模型
download_models() {
    print_info "下载AI模型..."
    
    # 检查Ollama是否安装
    if ! command -v ollama &> /dev/null; then
        print_info "安装Ollama..."
        curl -fsSL https://ollama.ai/install.sh | sh
    fi
    
    # 启动Ollama服务
    print_info "启动Ollama服务..."
    ollama serve &
    OLLAMA_PID=$!
    sleep 5
    
    # 下载模型
    models=("phi3:mini" "qwen:8b" "deepseek-coder:6.7b")
    
    for model in "${models[@]}"; do
        print_info "下载模型: $model"
        ollama pull "$model" || print_warning "模型 $model 下载失败，稍后重试"
    done
    
    print_success "模型下载完成"
}

# 创建配置文件
create_config_files() {
    print_info "创建配置文件..."
    
    # 创建.env文件
    cat > .env << EOF
# AI监理系统环境配置
APP_NAME="AI Monitor System"
APP_VERSION="2.1.0"
ENVIRONMENT="development"

# API配置
API_HOST="0.0.0.0"
API_PORT="8000"
API_KEY="your-secret-api-key"
JWT_SECRET="your-jwt-secret-key"
JWT_ALGORITHM="HS256"
JWT_EXPIRATION_HOURS="24"

# Ollama配置
OLLAMA_HOST="http://localhost:11434"
DEFAULT_MODEL="qwen:8b"
CODE_MODEL="deepseek-coder:6.7b"
EMBEDDING_MODEL="nomic-embed-text"

# Weaviate配置
WEAVIATE_URL="http://localhost:8080"
WEAVIATE_API_KEY=""

# 性能配置
MAX_WORKERS="12"
MEMORY_LIMIT_GB="32"
VECTOR_CACHE_SIZE_GB="16"

# 日志配置
LOG_LEVEL="INFO"
LOG_FILE="logs/ai_monitor.log"

# MCP配置
MCP_FILESYSTEM_PATHS="/Users/imac/Projects,/Users/imac/Documents"
MCP_GITHUB_TOKEN="your-github-token"
EOF
    
    # 创建监理规则配置
    cat > infrastructure/config/monitor_rules.json << 'EOF'
{
  "version": "2.1.0",
  "rules": [
    {
      "id": "PY001",
      "name": "未使用的导入",
      "severity": "warning",
      "pattern": "^import\\s+(\\w+)|^from\\s+\\S+\\s+import\\s+(\\w+)",
      "enabled": true
    },
    {
      "id": "PY002",
      "name": "代码复杂度过高",
      "severity": "warning",
      "threshold": 10,
      "enabled": true
    },
    {
      "id": "PY003",
      "name": "缺少文档字符串",
      "severity": "info",
      "enabled": true
    },
    {
      "id": "SEC001",
      "name": "潜在的安全问题",
      "severity": "error",
      "pattern": "eval\\(|exec\\(|__import__\\(",
      "enabled": true
    },
    {
      "id": "PERF001",
      "name": "性能优化建议",
      "severity": "info",
      "enabled": true
    }
  ]
}
EOF
    
    # 创建Docker Compose配置
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  weaviate:
    image: semitechnologies/weaviate:latest
    ports:
      - "8080:8080"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'text2vec-transformers'
      ENABLE_MODULES: 'text2vec-transformers'
      TRANSFORMERS_INFERENCE_API: 'http://t2v-transformers:8080'
      CLUSTER_HOSTNAME: 'node1'
    volumes:
      - weaviate_data:/var/lib/weaviate
    restart: unless-stopped

  t2v-transformers:
    image: semitechnologies/transformers-inference:sentence-transformers-multi-qa-MiniLM-L6-cos-v1
    environment:
      ENABLE_CUDA: '0'

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped

volumes:
  weaviate_data:
  redis_data:
  prometheus_data:
EOF
    
    print_success "配置文件创建完成"
}

# 启动服务
start_services() {
    print_info "启动服务..."
    
    # 启动Docker服务
    print_info "启动Docker容器..."
    docker-compose up -d
    
    # 等待服务就绪
    print_info "等待服务就绪..."
    sleep 10
    
    # 检查服务状态
    if curl -s http://localhost:8080/v1/.well-known/ready > /dev/null; then
        print_success "Weaviate 服务就绪"
    else
        print_warning "Weaviate 服务可能未就绪"
    fi
    
    print_success "所有服务已启动"
}

# 初始化系统
initialize_system() {
    print_info "初始化系统..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 初始化向量数据库
    python3 << EOF
import weaviate
client = weaviate.Client("http://localhost:8080")

# 创建Schema
schema = {
    "classes": [{
        "class": "Document",
        "description": "代码文档和知识库",
        "vectorizer": "text2vec-transformers",
        "properties": [
            {
                "name": "content",
                "dataType": ["text"],
                "description": "文档内容"
            },
            {
                "name": "metadata",
                "dataType": ["object"],
                "description": "元数据"
            },
            {
                "name": "embedding",
                "dataType": ["number[]"],
                "description": "向量嵌入"
            }
        ]
    }]
}

try:
    client.schema.create(schema)
    print("✓ 向量数据库初始化完成")
except:
    print("! 向量数据库已存在或初始化失败")
EOF
    
    print_success "系统初始化完成"
}

# 创建启动脚本
create_start_script() {
    cat > start.sh << 'EOF'
#!/bin/bash
# 启动AI监理系统

# 激活虚拟环境
source venv/bin/activate

# 启动Ollama（如果未运行）
if ! pgrep -x "ollama" > /dev/null; then
    echo "启动Ollama服务..."
    ollama serve &
    sleep 5
fi

# 启动API服务
echo "启动API服务..."
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

# 启动GUI（可选）
read -p "是否启动GUI界面？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python frontend/gui/gui_menu.py &
fi

echo "AI监理系统已启动！"
echo "API文档: http://localhost:8000/docs"
echo "按 Ctrl+C 停止服务"

# 等待中断信号
trap "kill $API_PID; exit" INT
wait
EOF
    
    chmod +x start.sh
    print_success "启动脚本创建完成"
}

# 主函数
main() {
    print_banner
    
    # 检查系统要求
    check_requirements
    
    # 创建项目结构
    create_project_structure
    
    # 安装依赖
    install_python_deps
    
    # 下载模型
    download_models
    
    # 创建配置文件
    create_config_files
    
    # 启动服务
    start_services
    
    # 初始化系统
    initialize_system
    
    # 创建启动脚本
    create_start_script
    
    print_success "🎉 AI监理系统安装完成！"
    echo ""
    print_info "启动系统: ./start.sh"
    print_info "API文档: http://localhost:8000/docs"
    print_info "配置文件: .env"
    echo ""
    print_warning "首次启动可能需要下载模型，请耐心等待"
}

# 执行主函数
main