"""
AI监理系统 - 最小可运行版本
只需要: pip install fastapi uvicorn httpx
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import httpx
import os

app = FastAPI(
    title="AI监理系统 Mini",
    description="最小化的AI代码监理API",
    version="1.0.0"
)

# 配置
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama3.2")

# 数据模型
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = DEFAULT_MODEL
    temperature: Optional[float] = 0.7

class CodeAnalyzeRequest(BaseModel):
    code: str
    language: Optional[str] = "python"
    
# API端点

@app.get("/")
async def root():
    """系统状态"""
    return {
        "status": "running",
        "service": "AI Monitor Mini",
        "ollama_host": OLLAMA_HOST,
        "default_model": DEFAULT_MODEL
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_HOST}/api/tags", timeout=5.0)
            models = response.json().get("models", [])
            return {
                "status": "healthy",
                "ollama": "connected",
                "available_models": [m["name"] for m in models]
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "ollama": "disconnected",
            "error": str(e)
        }

@app.post("/chat")
async def chat(request: ChatRequest):
    """聊天接口"""
    try:
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_HOST}/api/chat",
                json={
                    "model": request.model,
                    "messages": messages,
                    "temperature": request.temperature,
                    "stream": False
                },
                timeout=30.0
            )
            response.raise_for_status()
            
            data = response.json()
            return {
                "response": data.get("message", {}).get("content", ""),
                "model": request.model,
                "total_duration": data.get("total_duration", 0) / 1e9  # 转换为秒
            }
            
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"Ollama服务错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/code")
async def analyze_code(request: CodeAnalyzeRequest):
    """代码分析接口"""
    prompt = f"""作为代码审查专家，请分析以下{request.language}代码：

```{request.language}
{request.code}
```

请识别：
1. 潜在的bug
2. 性能问题
3. 代码风格问题
4. 安全隐患

以简洁的格式回复。"""

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_HOST}/api/chat",
                json={
                    "model": DEFAULT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "stream": False
                },
                timeout=60.0
            )
            response.raise_for_status()
            
            data = response.json()
            return {
                "analysis": data.get("message", {}).get("content", ""),
                "model": DEFAULT_MODEL,
                "duration": data.get("total_duration", 0) / 1e9
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/code")
async def generate_code(description: str, language: str = "python"):
    """代码生成接口"""
    prompt = f"请用{language}编写代码实现以下功能：\n{description}\n\n只返回代码，不要解释。"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_HOST}/api/chat",
                json={
                    "model": DEFAULT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "stream": False
                },
                timeout=60.0
            )
            response.raise_for_status()
            
            data = response.json()
            code = data.get("message", {}).get("content", "")
            
            # 清理代码块标记
            if "```" in code:
                lines = code.split("\n")
                code_lines = []
                in_code = False
                for line in lines:
                    if line.strip().startswith("```"):
                        in_code = not in_code
                        continue
                    if in_code:
                        code_lines.append(line)
                code = "\n".join(code_lines)
            
            return {
                "code": code.strip(),
                "language": language,
                "model": DEFAULT_MODEL
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 启动提示
@app.on_event("startup")
async def startup_event():
    print("🚀 AI监理系统Mini启动")
    print(f"📍 API地址: http://localhost:8000")
    print(f"📚 API文档: http://localhost:8000/docs")
    print(f"🤖 Ollama地址: {OLLAMA_HOST}")
    
    # 检查Ollama连接
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_HOST}/api/tags", timeout=5.0)
            models = response.json().get("models", [])
            if models:
                print(f"✅ 已连接到Ollama，可用模型: {[m['name'] for m in models]}")
            else:
                print("⚠️ Ollama已连接但没有模型，请运行: ollama pull llama3.2")
    except Exception as e:
        print(f"❌ 无法连接到Ollama: {e}")
        print("请确保Ollama正在运行: ollama serve")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
