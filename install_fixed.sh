#!/bin/bash
# AI监理系统 - 修复版安装脚本
# 使用最新兼容的包版本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 当前目录
CURRENT_DIR="$(pwd)"
INSTALL_DIR="$HOME/ai-monitor-local"

echo -e "${BLUE}AI监理系统 - 本地安装（修复版）${NC}"
echo "=================================="

# 1. 检查Python版本
echo -e "\n${GREEN}检查Python版本...${NC}"
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3.10 &> /dev/null; then
    PYTHON_CMD="python3.10"
elif command -v python3.9 &> /dev/null; then
    PYTHON_CMD="python3.9"
else
    echo -e "${RED}错误：需要Python 3.9或更高版本${NC}"
    echo "请先安装Python："
    echo "brew install python@3.11"
    exit 1
fi

echo "使用Python: $($PYTHON_CMD --version)"

# 2. 创建项目结构
echo -e "\n${GREEN}创建项目结构...${NC}"
mkdir -p "$INSTALL_DIR"/{api,core,frontend,logs,cache,data}
mkdir -p "$INSTALL_DIR"/api/{auth,endpoints,models}
mkdir -p "$INSTALL_DIR"/core/{llm,vector,voice}

# 3. 复制文件
echo -e "\n${GREEN}复制项目文件...${NC}"
cp "$CURRENT_DIR"/*.py "$INSTALL_DIR"/ 2>/dev/null || true

# 移动文件到正确位置
mv "$INSTALL_DIR"/ai-monitor-api-implementation.py "$INSTALL_DIR"/api/main.py 2>/dev/null || true
mv "$INSTALL_DIR"/ai-monitor-router-implementation.py "$INSTALL_DIR"/api/router.py 2>/dev/null || true
mv "$INSTALL_DIR"/ai-monitor-agent-implementation.py "$INSTALL_DIR"/api/monitor_agent.py 2>/dev/null || true
mv "$INSTALL_DIR"/ai-monitor-jwt-handler.py "$INSTALL_DIR"/api/auth/jwt_handler.py 2>/dev/null || true
mv "$INSTALL_DIR"/ai-monitor-models.py "$INSTALL_DIR"/api/models/models.py 2>/dev/null || true
mv "$INSTALL_DIR"/ai-monitor-ollama-client.py "$INSTALL_DIR"/core/llm/ollama_client.py 2>/dev/null || true
mv "$INSTALL_DIR"/ai-monitor-vector-client.py "$INSTALL_DIR"/core/vector/weaviate_client.py 2>/dev/null || true
mv "$INSTALL_DIR"/ai-monitor-tts-service.py "$INSTALL_DIR"/core/voice/tts_service.py 2>/dev/null || true
mv "$INSTALL_DIR"/ai-monitor-gui-implementation.py "$INSTALL_DIR"/frontend/gui_menu.py 2>/dev/null || true

# 4. 创建虚拟环境
echo -e "\n${GREEN}创建Python虚拟环境...${NC}"
cd "$INSTALL_DIR"
$PYTHON_CMD -m venv venv
source venv/bin/activate

# 5. 升级pip
echo -e "\n${GREEN}升级pip...${NC}"
pip install --upgrade pip setuptools wheel

# 6. 创建更新的requirements.txt
echo -e "\n${GREEN}创建requirements.txt...${NC}"
cat > requirements.txt << 'EOF'
# 核心框架 - 使用最新稳定版本
fastapi==0.111.0
uvicorn[standard]==0.30.1
pydantic==2.7.4
pydantic-settings==2.3.4

# 认证
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9

# HTTP客户端
httpx==0.27.0
aiofiles==24.1.0

# AI/LLM相关 - 使用兼容版本
ollama==0.3.0
openai==1.35.3

# 向量数据库 - 使用v3版本
weaviate-client==3.26.1

# 数据处理
numpy==1.26.4
pandas==2.2.2

# 工具库
python-dotenv==1.0.1
loguru==0.7.2
click==8.1.7
rich==13.7.1
jinja2==3.1.4
pyyaml==6.0.1

# 缓存和数据库
redis==5.0.7
cachetools==5.3.3

# Git集成
GitPython==3.1.43

# 监控
prometheus-client==0.20.0
psutil==5.9.8

# 测试
pytest==8.2.2
pytest-asyncio==0.23.7
pytest-cov==5.0.0

# 代码质量
black==24.4.2
ruff==0.4.10
mypy==1.10.1

# GUI依赖（如果需要）
# tkinter通常随Python一起安装

# 语音合成（可选）
# edge-tts==6.1.12
# pyttsx3==2.90
EOF

# 7. 安装Python包
echo -e "\n${GREEN}安装Python依赖...${NC}"
pip install -r requirements.txt || {
    echo -e "${YELLOW}部分包安装失败，尝试逐个安装...${NC}"
    while IFS= read -r line; do
        if [[ ! "$line" =~ ^# ]] && [[ ! -z "$line" ]]; then
            echo "安装: $line"
            pip install "$line" || echo -e "${YELLOW}跳过: $line${NC}"
        fi
    done < requirements.txt
}

# 8. 创建__init__.py文件
echo -e "\n${GREEN}创建__init__.py文件...${NC}"
touch api/__init__.py core/__init__.py
touch api/auth/__init__.py api/endpoints/__init__.py api/models/__init__.py
touch core/llm/__init__.py core/vector/__init__.py core/voice/__init__.py

# 9. 创建配置文件
echo -e "\n${GREEN}创建配置文件...${NC}"
cat > .env << 'EOF'
# API配置
API_HOST=0.0.0.0
API_PORT=8000
API_KEY=test-api-key
JWT_SECRET=your-secret-key-change-this

# Ollama配置
OLLAMA_HOST=http://localhost:11434
DEFAULT_MODEL=llama3.2
CODE_MODEL=qwen2.5-coder

# Redis配置（可选）
REDIS_URL=redis://localhost:6379

# 日志配置
LOG_LEVEL=INFO
EOF

# 10. 创建简单的启动脚本
echo -e "\n${GREEN}创建启动脚本...${NC}"
cat > start_simple.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate

echo "启动API服务..."
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
EOF
chmod +x start_simple.sh

# 11. 创建最小化的main.py
echo -e "\n${GREEN}创建简化的main.py...${NC}"
cat > api/main_simple.py << 'EOF'
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import httpx

app = FastAPI(title="AI监理系统", version="2.1.0")

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    model: str = "llama3.2"

@app.get("/")
async def root():
    return {"message": "AI监理系统运行中", "version": "2.1.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/v1/chat/completions")
async def chat(request: ChatRequest):
    try:
        # 调用Ollama
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": request.model,
                    "messages": request.messages,
                    "stream": False
                }
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# 12. 创建Docker Compose（简化版）
echo -e "\n${GREEN}创建Docker Compose配置...${NC}"
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # Redis缓存（可选）
  redis:
    image: redis:7-alpine
    container_name: ai-monitor-redis
    ports:
      - "6379:6379"
    volumes:
      - ./data/redis:/data
    command: redis-server --appendonly yes
    
  # Ollama Web UI（可选）
  ollama-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: ai-monitor-webui
    ports:
      - "3000:8080"
    environment:
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
    volumes:
      - ./data/webui:/app/backend/data
    extra_hosts:
      - "host.docker.internal:host-gateway"
EOF

# 13. 创建测试脚本
echo -e "\n${GREEN}创建测试脚本...${NC}"
cat > test_api.py << 'EOF'
import requests
import json

def test_health():
    response = requests.get("http://localhost:8000/health")
    print(f"Health Check: {response.json()}")

def test_chat():
    response = requests.post(
        "http://localhost:8000/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "Hello"}],
            "model": "llama3.2"
        }
    )
    print(f"Chat Response: {response.json()}")

if __name__ == "__main__":
    print("测试API...")
    test_health()
    # test_chat()  # 需要Ollama运行
EOF

echo -e "\n${GREEN}✅ 安装完成！${NC}"
echo ""
echo "安装目录: $INSTALL_DIR"
echo ""
echo "下一步："
echo "1. 安装并启动Ollama："
echo "   brew install ollama"
echo "   ollama serve"
echo ""
echo "2. 下载模型："
echo "   ollama pull llama3.2"
echo "   ollama pull qwen2.5-coder"
echo ""
echo "3. 启动API服务："
echo "   cd $INSTALL_DIR"
echo "   ./start_simple.sh"
echo ""
echo "4. 测试API："
echo "   python test_api.py"
echo ""
echo "可选："
echo "- 启动Redis: docker-compose up -d redis"
echo "- 启动Web UI: docker-compose up -d ollama-webui"
