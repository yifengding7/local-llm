# core/llm/ollama_client.py
"""
Ollama客户端 - 本地大语言模型运行时
优化Apple M3 Max性能，支持多模型管理和流式响应
"""

import httpx
import asyncio
import json
from typing import List, Dict, Any, Optional, AsyncGenerator, Union
from datetime import datetime
import time
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import os
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)

class ModelStatus(Enum):
    """模型状态"""
    NOT_FOUND = "not_found"
    DOWNLOADING = "downloading"
    READY = "ready"
    LOADING = "loading"
    RUNNING = "running"
    ERROR = "error"

@dataclass
class ModelInfo:
    """模型信息"""
    name: str
    size_bytes: int
    modified_at: str
    digest: str
    status: ModelStatus
    context_length: int = 4096
    embedding_dimension: Optional[int] = None
    
@dataclass
class GenerationStats:
    """生成统计信息"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_eval_duration_ms: float
    eval_duration_ms: float
    total_duration_ms: float
    tokens_per_second: float

class ModelCache:
    """模型响应缓存"""
    
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
    
    def get(self, key: str) -> Optional[str]:
        """获取缓存响应"""
        if key in self.cache:
            self.access_times[key] = time.time()
            return self.cache[key]
        return None
    
    def put(self, key: str, value: str):
        """缓存响应"""
        # 如果缓存满了，删除最旧的条目
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times.items(), key=lambda x: x[1])[0]
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
        
        self.cache[key] = value
        self.access_times[key] = time.time()

class OllamaClient:
    """Ollama客户端主类"""
    
    def __init__(self, 
                 base_url: str = "http://localhost:11434",
                 timeout: float = 300.0,
                 max_retries: int = 3):
        
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        
        # HTTP客户端配置
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        )
        
        # 模型缓存
        self.model_cache = ModelCache()
        self.loaded_models = {}
        self.model_stats = {}
        
        # 性能监控
        self.request_times = deque(maxlen=1000)
        self.token_counts = deque(maxlen=1000)
    
    async def list_models(self) -> List[ModelInfo]:
        """列出所有可用模型"""
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            
            data = response.json()
            models = []
            
            for model_data in data.get("models", []):
                model = ModelInfo(
                    name=model_data["name"],
                    size_bytes=model_data.get("size", 0),
                    modified_at=model_data.get("modified_at", ""),
                    digest=model_data.get("digest", ""),
                    status=ModelStatus.READY,
                    context_length=self._get_context_length(model_data["name"])
                )
                models.append(model)
                self.loaded_models[model.name] = model
            
            return models
            
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    async def pull_model(self, model_name: str, show_progress: bool = True) -> bool:
        """下载模型"""
        try:
            # 流式下载，显示进度
            async with self.client.stream(
                "POST",
                "/api/pull",
                json={"name": model_name, "stream": show_progress}
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        
                        if show_progress and "status" in data:
                            status = data["status"]
                            
                            if "pulling" in status:
                                # 下载进度
                                completed = data.get("completed", 0)
                                total = data.get("total", 0)
                                if total > 0:
                                    progress = completed / total * 100
                                    logger.info(f"Downloading {model_name}: {progress:.1f}%")
                            else:
                                logger.info(f"{model_name}: {status}")
                        
                        if "error" in data:
                            logger.error(f"Pull error: {data['error']}")
                            return False
            
            logger.info(f"Successfully pulled model: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False
    
    async def chat(self,
                   model: str,
                   messages: List[Dict[str, str]],
                   temperature: float = 0.7,
                   max_tokens: Optional[int] = None,
                   top_p: float = 1.0,
                   top_k: int = 40,
                   repeat_penalty: float = 1.1,
                   seed: Optional[int] = None,
                   stop: Optional[List[str]] = None,
                   stream: bool = False) -> Union[Dict[str, Any], AsyncGenerator[Dict[str, Any], None]]:
        """聊天接口"""
        
        # 构建请求
        request_data = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "repeat_penalty": repeat_penalty
            }
        }
        
        if max_tokens:
            request_data["options"]["num_predict"] = max_tokens
        if seed is not None:
            request_data["options"]["seed"] = seed
        if stop:
            request_data["options"]["stop"] = stop
        
        # 生成缓存键
        cache_key = self._generate_cache_key("chat", request_data)
        
        # 检查缓存（仅非流式）
        if not stream:
            cached = self.model_cache.get(cache_key)
            if cached:
                logger.debug("Cache hit for chat request")
                return json.loads(cached)
        
        start_time = time.time()
        
        try:
            if stream:
                return self._stream_chat(request_data, start_time)
            else:
                response = await self.client.post("/api/chat", json=request_data)
                response.raise_for_status()
                
                result = response.json()
                
                # 记录统计
                self._record_stats(result, start_time)
                
                # 缓存结果
                self.model_cache.put(cache_key, json.dumps(result))
                
                return result
                
        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise
    
    async def _stream_chat(self, request_data: Dict[str, Any], start_time: float) -> AsyncGenerator[Dict[str, Any], None]:
        """流式聊天响应"""
        total_tokens = 0
        
        try:
            async with self.client.stream("POST", "/api/chat", json=request_data) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line:
                        chunk = json.loads(line)
                        
                        # 统计token
                        if "message" in chunk and "content" in chunk["message"]:
                            total_tokens += len(chunk["message"]["content"].split()) // 4
                        
                        yield chunk
                        
                        # 如果是最后一个chunk，记录统计
                        if chunk.get("done", False):
                            self._record_stream_stats(total_tokens, start_time)
                            
        except Exception as e:
            logger.error(f"Stream chat error: {e}")
            raise
    
    async def generate(self,
                      model: str,
                      prompt: str,
                      temperature: float = 0.7,
                      max_tokens: Optional[int] = None,
                      stream: bool = False,
                      **kwargs) -> Union[str, AsyncGenerator[str, None]]:
        """文本生成接口"""
        
        request_data = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                **kwargs
            }
        }
        
        if max_tokens:
            request_data["options"]["num_predict"] = max_tokens
        
        try:
            if stream:
                return self._stream_generate(request_data)
            else:
                response = await self.client.post("/api/generate", json=request_data)
                response.raise_for_status()
                
                result = response.json()
                return result["response"]
                
        except Exception as e:
            logger.error(f"Generate error: {e}")
            raise
    
    async def _stream_generate(self, request_data: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """流式生成响应"""
        try:
            async with self.client.stream("POST", "/api/generate", json=request_data) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line:
                        chunk = json.loads(line)
                        if "response" in chunk:
                            yield chunk["response"]
                            
        except Exception as e:
            logger.error(f"Stream generate error: {e}")
            raise
    
    async def embeddings(self,
                        model: str,
                        prompt: Union[str, List[str]],
                        truncate: bool = True) -> Dict[str, Any]:
        """生成文本嵌入"""
        
        # 确保prompt是列表
        if isinstance(prompt, str):
            prompts = [prompt]
        else:
            prompts = prompt
        
        embeddings = []
        
        for p in prompts:
            request_data = {
                "model": model,
                "prompt": p
            }
            
            try:
                response = await self.client.post("/api/embeddings", json=request_data)
                response.raise_for_status()
                
                result = response.json()
                embeddings.append(result["embedding"])
                
            except Exception as e:
                logger.error(f"Embedding error for prompt: {e}")
                # 返回零向量作为失败情况
                embeddings.append([0.0] * 768)  # 假设768维
        
        return {
            "embeddings": embeddings if len(embeddings) > 1 else embeddings[0],
            "model": model,
            "prompt_tokens": sum(len(p.split()) for p in prompts)
        }
    
    async def warm_up_models(self, models: Optional[List[str]] = None):
        """预热模型 - 加载到内存"""
        if models is None:
            # 默认预热常用模型
            models = ["qwen:8b", "deepseek-coder:6.7b", "phi3:mini"]
        
        logger.info(f"Warming up models: {models}")
        
        for model in models:
            try:
                # 发送一个简单的请求来加载模型
                await self.generate(
                    model=model,
                    prompt="Hello",
                    max_tokens=1
                )
                logger.info(f"Model {model} warmed up")
                
            except Exception as e:
                logger.warning(f"Failed to warm up model {model}: {e}")
    
    async def unload_model(self, model: str):
        """卸载模型释放内存"""
        try:
            # Ollama API可能没有直接的卸载接口
            # 这里可以通过加载一个小模型来间接释放内存
            logger.info(f"Unloading model: {model}")
            
            # 从缓存中移除
            if model in self.loaded_models:
                del self.loaded_models[model]
                
        except Exception as e:
            logger.error(f"Failed to unload model {model}: {e}")
    
    async def get_model_info(self, model: str) -> Optional[ModelInfo]:
        """获取模型详细信息"""
        try:
            response = await self.client.post("/api/show", json={"name": model})
            response.raise_for_status()
            
            data = response.json()
            
            # 解析模型信息
            modelfile = data.get("modelfile", "")
            parameters = data.get("parameters", "")
            
            # 提取上下文长度
            context_length = 4096  # 默认值
            if "num_ctx" in parameters:
                # 解析参数找到context长度
                for line in parameters.split('\n'):
                    if "num_ctx" in line:
                        try:
                            context_length = int(line.split()[-1])
                        except:
                            pass
            
            return ModelInfo(
                name=model,
                size_bytes=data.get("size", 0),
                modified_at=data.get("modified_at", ""),
                digest=data.get("digest", ""),
                status=ModelStatus.READY,
                context_length=context_length
            )
            
        except Exception as e:
            logger.error(f"Failed to get model info for {model}: {e}")
            return None
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            response = await self.client.get("/")
            return response.status_code == 200
        except Exception:
            return False
    
    def _get_context_length(self, model_name: str) -> int:
        """根据模型名称猜测上下文长度"""
        context_map = {
            "phi3": 4096,
            "qwen": 8192,
            "deepseek": 16384,
            "llama": 4096,
            "mistral": 8192
        }
        
        for key, length in context_map.items():
            if key in model_name.lower():
                return length
        
        return 4096  # 默认值
    
    def _generate_cache_key(self, method: str, data: Dict[str, Any]) -> str:
        """生成缓存键"""
        import hashlib
        
        # 移除流式标志
        cache_data = data.copy()
        cache_data.pop("stream", None)
        
        key_str = f"{method}:{json.dumps(cache_data, sort_keys=True)}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _record_stats(self, result: Dict[str, Any], start_time: float):
        """记录统计信息"""
        duration = (time.time() - start_time) * 1000
        self.request_times.append(duration)
        
        # 提取token统计
        if "eval_count" in result:
            self.token_counts.append(result["eval_count"])
        
        # 更新模型统计
        model = result.get("model", "unknown")
        if model not in self.model_stats:
            self.model_stats[model] = {
                "requests": 0,
                "total_tokens": 0,
                "total_time_ms": 0
            }
        
        stats = self.model_stats[model]
        stats["requests"] += 1
        stats["total_tokens"] += result.get("eval_count", 0) + result.get("prompt_eval_count", 0)
        stats["total_time_ms"] += duration
    
    def _record_stream_stats(self, total_tokens: int, start_time: float):
        """记录流式响应统计"""
        duration = (time.time() - start_time) * 1000
        self.request_times.append(duration)
        self.token_counts.append(total_tokens)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        if not self.request_times:
            return {
                "total_requests": 0,
                "avg_latency_ms": 0,
                "avg_tokens": 0,
                "models": {}
            }
        
        return {
            "total_requests": len(self.request_times),
            "avg_latency_ms": sum(self.request_times) / len(self.request_times),
            "min_latency_ms": min(self.request_times),
            "max_latency_ms": max(self.request_times),
            "avg_tokens": sum(self.token_counts) / len(self.token_counts) if self.token_counts else 0,
            "models": self.model_stats,
            "cache_size": len(self.model_cache.cache)
        }
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
        logger.info("Ollama client closed")

# 便捷函数
async def create_ollama_client(base_url: str = None) -> OllamaClient:
    """创建Ollama客户端实例"""
    if base_url is None:
        base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
    client = OllamaClient(base_url=base_url)
    
    # 检查连接
    if not await client.health_check():
        logger.warning("Ollama service is not available")
    
    return client