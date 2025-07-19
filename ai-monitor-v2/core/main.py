#!/usr/bin/env python3
"""
AI监理系统v2.1核心引擎
支持FastAPI 0.116.1、Pydantic 2.11.7、Uvicorn 0.35.0
M3 Max硬件优化版本
"""

import asyncio
import uvloop
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List
import time
import psutil
import os
from datetime import datetime

# 使用清华源安装的依赖
try:
    from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.gzip import GZipMiddleware
    from fastapi.responses import JSONResponse, StreamingResponse
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from pydantic import BaseModel, Field, ConfigDict
    from pydantic_settings import BaseSettings
    import uvicorn
    import httpx
    import aioredis
    import asyncpg
    from prometheus_client import Counter, Histogram, Gauge, generate_latest
    from prometheus_client.exposition import CONTENT_TYPE_LATEST
except ImportError as e:
    print(f"依赖包缺失: {e}")
    print("请运行: pip install -r requirements.txt")
    exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus指标
REQUEST_COUNT = Counter('ai_monitor_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('ai_monitor_request_duration_seconds', 'Request duration')
ACTIVE_CONNECTIONS = Gauge('ai_monitor_active_connections', 'Active connections')
MEMORY_USAGE = Gauge('ai_monitor_memory_usage_bytes', 'Memory usage in bytes')
CPU_USAGE = Gauge('ai_monitor_cpu_usage_percent', 'CPU usage percentage')

class Settings(BaseSettings):
    """应用配置"""
    model_config = ConfigDict(env_file=".env")
    
    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # 数据库配置
    database_url: str = "postgresql://user:password@localhost/ai_monitor"
    redis_url: str = "redis://localhost:6379"
    
    # Ollama配置
    ollama_url: str = "http://localhost:11434"
    
    # Weaviate配置
    weaviate_url: str = "http://localhost:8080"
    
    # 性能配置
    max_workers: int = 12  # M3 Max 12核
    memory_limit: int = 64 * 1024 * 1024 * 1024  # 64GB
    
    # 安全配置
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

settings = Settings()

# 数据模型
class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: int
    version: str
    uptime: int
    system: Dict[str, Any]

class LLMRequest(BaseModel):
    """LLM请求模型"""
    model: str = Field(..., description="模型名称")
    prompt: str = Field(..., description="提示词")
    stream: bool = Field(False, description="是否流式返回")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int = Field(1024, ge=1, le=4096, description="最大令牌数")

class LLMResponse(BaseModel):
    """LLM响应模型"""
    response: str
    model: str
    tokens_used: int
    processing_time: float
    timestamp: int

class VectorRequest(BaseModel):
    """向量请求模型"""
    text: str = Field(..., description="待向量化的文本")
    collection: str = Field("default", description="集合名称")

class VectorResponse(BaseModel):
    """向量响应模型"""
    embedding: List[float]
    dimension: int
    text: str
    collection: str
    timestamp: int

class SystemMetrics(BaseModel):
    """系统指标"""
    cpu_percent: float
    memory_percent: float
    memory_used: int
    memory_total: int
    disk_usage: Dict[str, Any]
    network_io: Dict[str, Any]
    load_average: List[float]
    timestamp: int

class AIMonitorCore:
    """AI监理系统核心引擎"""
    
    def __init__(self):
        self.start_time = time.time()
        self.redis_client: Optional[aioredis.Redis] = None
        self.db_pool: Optional[asyncpg.Pool] = None
        self.ollama_client: Optional[httpx.AsyncClient] = None
        self.weaviate_client: Optional[httpx.AsyncClient] = None
        self.active_connections = 0
        
    async def initialize(self):
        """初始化核心组件"""
        logger.info("🚀 初始化AI监理系统v2.1核心引擎...")
        
        # 初始化Redis
        try:
            self.redis_client = await aioredis.from_url(settings.redis_url)
            await self.redis_client.ping()
            logger.info("✅ Redis连接成功")
        except Exception as e:
            logger.warning(f"⚠️ Redis连接失败: {e}")
            self.redis_client = None
        
        # 初始化数据库连接池
        try:
            self.db_pool = await asyncpg.create_pool(
                settings.database_url,
                min_size=5,
                max_size=20,
                command_timeout=10
            )
            logger.info("✅ 数据库连接池创建成功")
        except Exception as e:
            logger.warning(f"⚠️ 数据库连接失败: {e}")
            self.db_pool = None
        
        # 初始化Ollama客户端
        self.ollama_client = httpx.AsyncClient(
            base_url=settings.ollama_url,
            timeout=30.0
        )
        
        # 初始化Weaviate客户端
        self.weaviate_client = httpx.AsyncClient(
            base_url=settings.weaviate_url,
            timeout=30.0
        )
        
        logger.info("✅ 核心引擎初始化完成")
    
    async def cleanup(self):
        """清理资源"""
        logger.info("🧹 清理系统资源...")
        
        if self.redis_client:
            await self.redis_client.close()
        
        if self.db_pool:
            await self.db_pool.close()
        
        if self.ollama_client:
            await self.ollama_client.aclose()
        
        if self.weaviate_client:
            await self.weaviate_client.aclose()
        
        logger.info("✅ 资源清理完成")
    
    async def process_llm_request(self, request: LLMRequest) -> LLMResponse:
        """处理LLM请求"""
        start_time = time.time()
        
        try:
            # 发送请求到Ollama
            response = await self.ollama_client.post(
                "/api/generate",
                json={
                    "model": request.model,
                    "prompt": request.prompt,
                    "stream": request.stream,
                    "options": {
                        "temperature": request.temperature,
                        "num_predict": request.max_tokens
                    }
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Ollama请求失败: {response.text}"
                )
            
            result = response.json()
            processing_time = time.time() - start_time
            
            return LLMResponse(
                response=result.get("response", ""),
                model=request.model,
                tokens_used=result.get("prompt_eval_count", 0) + result.get("eval_count", 0),
                processing_time=processing_time,
                timestamp=int(time.time())
            )
            
        except Exception as e:
            logger.error(f"LLM处理错误: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def process_vector_request(self, request: VectorRequest) -> VectorResponse:
        """处理向量化请求"""
        start_time = time.time()
        
        try:
            # 使用nomic-embed-text模型进行向量化
            response = await self.ollama_client.post(
                "/api/embeddings",
                json={
                    "model": "nomic-embed-text",
                    "prompt": request.text
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"向量化请求失败: {response.text}"
                )
            
            result = response.json()
            embedding = result.get("embedding", [])
            
            # 缓存向量结果
            if self.redis_client:
                cache_key = f"vector:{hash(request.text)}"
                await self.redis_client.setex(
                    cache_key,
                    3600,  # 1小时过期
                    str(embedding)
                )
            
            return VectorResponse(
                embedding=embedding,
                dimension=len(embedding),
                text=request.text,
                collection=request.collection,
                timestamp=int(time.time())
            )
            
        except Exception as e:
            logger.error(f"向量化处理错误: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_system_metrics(self) -> SystemMetrics:
        """获取系统指标"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        # 更新Prometheus指标
        CPU_USAGE.set(cpu_percent)
        MEMORY_USAGE.set(memory.used)
        
        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used=memory.used,
            memory_total=memory.total,
            disk_usage={
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            },
            network_io={
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            },
            load_average=os.getloadavg(),
            timestamp=int(time.time())
        )

# 全局核心引擎实例
core = AIMonitorCore()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    await core.initialize()
    
    # 启动系统监控
    asyncio.create_task(system_monitor())
    
    yield
    
    # 关闭时清理
    await core.cleanup()

# 创建FastAPI应用
app = FastAPI(
    title="AI监理系统v2.1",
    description="基于M3 Max优化的AI监理系统核心引擎",
    version="2.1.0",
    lifespan=lifespan
)

# 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# 认证安全
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户"""
    # 这里可以添加JWT验证逻辑
    return {"user": "admin"}

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """性能指标中间件"""
    start_time = time.time()
    
    # 增加活跃连接
    core.active_connections += 1
    ACTIVE_CONNECTIONS.set(core.active_connections)
    
    try:
        response = await call_next(request)
        
        # 记录指标
        duration = time.time() - start_time
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        REQUEST_DURATION.observe(duration)
        
        return response
    finally:
        # 减少活跃连接
        core.active_connections -= 1
        ACTIVE_CONNECTIONS.set(core.active_connections)

# API路由
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    uptime = int(time.time() - core.start_time)
    system_metrics = core.get_system_metrics()
    
    return HealthResponse(
        status="healthy",
        timestamp=int(time.time()),
        version="2.1.0",
        uptime=uptime,
        system={
            "cpu_percent": system_metrics.cpu_percent,
            "memory_percent": system_metrics.memory_percent,
            "active_connections": core.active_connections,
            "ollama_available": await check_ollama_health(),
            "weaviate_available": await check_weaviate_health()
        }
    )

@app.post("/llm/generate", response_model=LLMResponse)
async def generate_text(
    request: LLMRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """LLM文本生成"""
    return await core.process_llm_request(request)

@app.post("/vector/embed", response_model=VectorResponse)
async def embed_text(
    request: VectorRequest,
    user: dict = Depends(get_current_user)
):
    """文本向量化"""
    return await core.process_vector_request(request)

@app.get("/metrics/system", response_model=SystemMetrics)
async def get_system_metrics():
    """获取系统指标"""
    return core.get_system_metrics()

@app.get("/metrics/prometheus")
async def get_prometheus_metrics():
    """Prometheus指标端点"""
    return StreamingResponse(
        iter([generate_latest().decode()]),
        media_type=CONTENT_TYPE_LATEST
    )

@app.get("/status")
async def get_status():
    """获取服务状态"""
    return {
        "service": "AI监理系统v2.1",
        "version": "2.1.0",
        "uptime": int(time.time() - core.start_time),
        "timestamp": int(time.time()),
        "environment": {
            "python_version": f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}.{psutil.sys.version_info.micro}",
            "platform": psutil.platform.platform(),
            "architecture": psutil.platform.machine(),
            "processor": psutil.platform.processor()
        }
    }

async def check_ollama_health() -> bool:
    """检查Ollama服务健康状态"""
    try:
        response = await core.ollama_client.get("/api/tags", timeout=5.0)
        return response.status_code == 200
    except:
        return False

async def check_weaviate_health() -> bool:
    """检查Weaviate服务健康状态"""
    try:
        response = await core.weaviate_client.get("/v1/meta", timeout=5.0)
        return response.status_code == 200
    except:
        return False

async def system_monitor():
    """系统监控任务"""
    while True:
        try:
            # 更新系统指标
            metrics = core.get_system_metrics()
            
            # 检查资源使用情况
            if metrics.memory_percent > 85:
                logger.warning(f"内存使用率过高: {metrics.memory_percent}%")
            
            if metrics.cpu_percent > 90:
                logger.warning(f"CPU使用率过高: {metrics.cpu_percent}%")
            
            # 等待下次检查
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"系统监控错误: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    # 使用uvloop提升性能
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    
    # 启动服务
    logger.info("🚀 启动AI监理系统v2.1核心引擎")
    logger.info(f"🌐 服务地址: http://{settings.host}:{settings.port}")
    logger.info(f"📊 健康检查: http://{settings.host}:{settings.port}/health")
    logger.info(f"📈 指标监控: http://{settings.host}:{settings.port}/metrics/prometheus")
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1,  # 使用1个worker，利用异步并发
        loop="uvloop",
        log_level="info",
        access_log=True,
        use_colors=True
    )