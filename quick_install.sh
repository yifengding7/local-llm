#!/bin/bash
# 快速安装脚本 - 极简版

echo "🚀 AI监理系统 - 快速安装"
echo "========================"

# 1. 检查Ollama
if ! command -v ollama &> /dev/null; then
    echo "❌ 请先安装Ollama："
    echo "brew install ollama"
    exit 1
fi

# 2. 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 请先安装Python 3"
    exit 1
fi

# 3. 创建最小项目
mkdir -p ~/ai-monitor-mini
cd ~/ai-monitor-mini

# 4. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 5. 安装最少依赖
pip install fastapi uvicorn httpx

# 6. 创建单文件API
cat > app.py << 'EOF'
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
import httpx
import asyncio

app = FastAPI(title="AI监理系统 Mini")

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    model: str = "llama3.2"

@app.get("/")
def read_root():
    return {"status": "AI监理系统运行中"}

@app.post("/chat")
async def chat(request: ChatRequest):
    # 转换消息格式
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    
    # 调用Ollama
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:11434/api/chat",
            json={
                "model": request.model,
                "messages": messages,
                "stream": False
            },
            timeout=30.0
        )
        return response.json()

# 代码分析端点
@app.post("/analyze")
async def analyze_code(code: str):
    prompt = f"分析以下代码，找出潜在问题：\n\n{code}"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "qwen2.5-coder",
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            },
            timeout=30.0
        )
        return response.json()
EOF

# 7. 创建启动脚本
cat > start.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
echo "启动服务: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
uvicorn app:app --reload --host 0.0.0.0 --port 8000
EOF
chmod +x start.sh

# 8. 创建测试脚本
cat > test.py << 'EOF'
import requests

# 测试聊天
response = requests.post(
    "http://localhost:8000/chat",
    json={
        "messages": [{"role": "user", "content": "你好"}],
        "model": "llama3.2"
    }
)
print("聊天测试:", response.json())
EOF

echo ""
echo "✅ 安装完成！"
echo ""
echo "使用方法："
echo "1. 启动Ollama: ollama serve"
echo "2. 下载模型: ollama pull llama3.2"
echo "3. 启动API: cd ~/ai-monitor-mini && ./start.sh"
echo "4. 访问: http://localhost:8000/docs"
