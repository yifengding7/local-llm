# api/main.py
"""
AI监理系统 v2.1 - FastAPI主服务
支持OpenAI兼容API、智能路由、监理功能
"""

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from typing import Dict, Any, Optional, List
import json
import asyncio
from datetime import datetime
import logging

# 导入自定义模块
from .router import Router, TaskType
from .monitor_agent import MonitorAgent
from .auth.jwt_handler import JWTHandler
from .models.request import ChatRequest, MonitorRequest, VoiceRequest
from .models.response import ChatResponse, MonitorResponse
from ..core.llm.ollama_client import OllamaClient
from ..core.vector.weaviate_client import WeaviateClient
from ..core.voice.tts_service import TTSService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局服务实例
router: Optional[Router] = None
monitor_agent: Optional[MonitorAgent] = None
ollama_client: Optional[OllamaClient] = None
vector_client: Optional[WeaviateClient] = None
tts_service: Optional[TTSService] = None
jwt_handler: Optional[JWTHandler] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global router, monitor_agent, ollama_client, vector_client, tts_service, jwt_handler
    
    logger.info("🚀 启动AI监理系统 v2.1...")
    
    # 初始化服务
    router = Router()
    monitor_agent = MonitorAgent()
    ollama_client = OllamaClient()
    vector_client = WeaviateClient()
    tts_service = TTSService()
    jwt_handler = JWTHandler()
    
    # 预热模型
    await ollama_client.warm_up_models()
    
    logger.info("✅ 系统启动完成")
    
    yield
    
    # 清理资源
    logger.info("🔄 正在关闭系统...")
    await ollama_client.close()
    await vector_client.close()

# 创建FastAPI应用
app = FastAPI(
    title="AI监理系统 v2.1",
    description="高性能AI代码监理和辅助系统",
    version="2.1.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 认证依赖
async def verify_token(request: Request):
    """JWT认证"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")
    
    try:
        payload = jwt_handler.verify_token(token)
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

# API端点

@app.get("/")
async def root():
    """系统状态"""
    return {
        "service": "AI Monitor System",
        "version": "2.1.0",
        "status": "online",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatRequest,
    user=Depends(verify_token)
):
    """OpenAI兼容的聊天接口"""
    try:
        # 路由到合适的模型
        model_name = router.route(TaskType.CHAT, request.dict())
        
        # 如果需要检索增强
        if request.use_rag:
            # 向量检索
            context = await vector_client.search(
                query=request.messages[-1]["content"],
                limit=5
            )
            # 构建增强提示
            enhanced_prompt = _build_rag_prompt(request.messages, context)
            request.messages[-1]["content"] = enhanced_prompt
        
        # 生成响应
        if request.stream:
            return StreamingResponse(
                _stream_chat_response(model_name, request),
                media_type="text/event-stream"
            )
        else:
            response = await ollama_client.chat(
                model=model_name,
                messages=request.messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            return ChatResponse(
                id=f"chatcmpl-{datetime.utcnow().timestamp()}",
                choices=[{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response["message"]["content"]
                    },
                    "finish_reason": "stop"
                }],
                usage=response.get("usage", {})
            )
            
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/monitor/analyze")
async def analyze_code(
    request: MonitorRequest,
    user=Depends(verify_token)
):
    """代码监理分析"""
    try:
        # 分析代码
        issues = await monitor_agent.analyze_code(
            file_path=request.file_path,
            rules=request.rules
        )
        
        # 如果启用自动修复
        if request.auto_fix and issues:
            patch = await monitor_agent.generate_patch(issues)
            if request.apply_patch:
                await monitor_agent.apply_patch(request.file_path, patch)
        
        return MonitorResponse(
            file_path=request.file_path,
            issues=issues,
            severity_counts=_count_severities(issues),
            patch=patch if request.auto_fix else None,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Monitor error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/voice/tts")
async def text_to_speech(
    request: VoiceRequest,
    user=Depends(verify_token)
):
    """文本转语音"""
    try:
        # 生成语音
        audio_data = await tts_service.synthesize(
            text=request.text,
            voice=request.voice,
            speed=request.speed
        )
        
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"attachment; filename=speech.mp3"
            }
        )
        
    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/embeddings")
async def create_embeddings(
    request: Dict[str, Any],
    user=Depends(verify_token)
):
    """生成文本嵌入"""
    try:
        model_name = router.route(TaskType.EMBEDDING, request)
        
        embeddings = await ollama_client.embeddings(
            model=model_name,
            prompt=request["input"]
        )
        
        return {
            "object": "list",
            "data": [{
                "object": "embedding",
                "embedding": embeddings["embedding"],
                "index": 0
            }],
            "model": model_name,
            "usage": {
                "prompt_tokens": len(request["input"].split()),
                "total_tokens": len(request["input"].split())
            }
        }
        
    except Exception as e:
        logger.error(f"Embedding error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 工具函数

async def _stream_chat_response(model_name: str, request: ChatRequest):
    """流式响应生成器"""
    try:
        async for chunk in ollama_client.chat_stream(
            model=model_name,
            messages=request.messages,
            temperature=request.temperature
        ):
            # 格式化为SSE
            data = {
                "id": f"chatcmpl-{datetime.utcnow().timestamp()}",
                "object": "chat.completion.chunk",
                "created": int(datetime.utcnow().timestamp()),
                "model": model_name,
                "choices": [{
                    "index": 0,
                    "delta": {
                        "content": chunk.get("message", {}).get("content", "")
                    },
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(data)}\n\n"
        
        # 发送结束标记
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Stream error: {str(e)}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

def _build_rag_prompt(messages: List[Dict], context: List[Dict]) -> str:
    """构建RAG增强提示"""
    context_text = "\n\n".join([
        f"[相关文档 {i+1}]\n{doc['content']}"
        for i, doc in enumerate(context)
    ])
    
    original_prompt = messages[-1]["content"]
    
    return f"""基于以下相关文档回答问题：

{context_text}

问题：{original_prompt}

请基于提供的文档内容回答，如果文档中没有相关信息，请说明。"""

def _count_severities(issues: List[Dict]) -> Dict[str, int]:
    """统计问题严重程度"""
    counts = {"error": 0, "warning": 0, "info": 0}
    for issue in issues:
        severity = issue.get("severity", "info")
        counts[severity] = counts.get(severity, 0) + 1
    return counts

# 性能监控端点

@app.get("/v1/metrics")
async def get_metrics(user=Depends(verify_token)):
    """系统性能指标"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "models": {
            "loaded": await ollama_client.list_models(),
            "active_requests": router.get_active_requests()
        },
        "vector_db": {
            "document_count": await vector_client.get_count(),
            "index_size": await vector_client.get_index_size()
        },
        "performance": {
            "avg_latency_ms": router.get_avg_latency(),
            "requests_per_second": router.get_rps(),
            "error_rate": router.get_error_rate()
        }
    }

# 健康检查

@app.get("/health")
async def health_check():
    """健康检查端点"""
    checks = {
        "api": "healthy",
        "ollama": "unknown",
        "weaviate": "unknown",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        # 检查Ollama
        await ollama_client.health_check()
        checks["ollama"] = "healthy"
    except:
        checks["ollama"] = "unhealthy"
    
    try:
        # 检查Weaviate
        await vector_client.health_check()
        checks["weaviate"] = "healthy"
    except:
        checks["weaviate"] = "unhealthy"
    
    # 判断总体健康状态
    overall_healthy = all(v == "healthy" for k, v in checks.items() if k != "timestamp")
    status_code = 200 if overall_healthy else 503
    
    return JSONResponse(content=checks, status_code=status_code)

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )