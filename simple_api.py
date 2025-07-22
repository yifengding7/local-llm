#!/usr/bin/env python3
"""
简化版API服务 - 专门用于测试LLM控制台
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import time
import psutil

app = FastAPI(title="AI监理系统", version="2.2.0")

start_time = time.time()

@app.get("/")
async def root():
    return {"message": "AI监理系统 v2.2 运行中", "status": "ok"}

@app.get("/health")
async def health_check():
    """健康检查接口"""
    uptime = int(time.time() - start_time)
    return {
        "status": "healthy",
        "uptime": uptime,
        "version": "2.2.0",
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }
    }

@app.get("/docs")
async def get_docs():
    """API文档重定向"""
    return {"message": "API文档可用", "docs_url": "/docs"}

@app.get("/api/status")
async def api_status():
    """API状态"""
    return {
        "ai_monitor": True,
        "ollama": False,  # 简化版暂不检查
        "weaviate": False,  # 简化版暂不检查
        "go_api": False,
        "rust_engine": False
    }

if __name__ == "__main__":
    print("🚀 启动简化版AI监理系统...")
    print("📡 服务地址: http://localhost:8000")
    print("🏥 健康检查: http://localhost:8000/health")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )