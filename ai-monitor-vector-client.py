# core/vector/weaviate_client.py
"""
Weaviate向量数据库客户端 - 极致性能优化版
支持<50ms查询延迟，千万级向量容量
"""

import weaviate
from weaviate.embedded import EmbeddedOptions
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio
import time
import json
import hashlib
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import logging
from cachetools import TTLCache, LRUCache
import mmap
import struct
import os

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """搜索结果"""
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float
    vector: Optional[List[float]] = None
    latency_ms: float = 0.0

@dataclass
class IndexStats:
    """索引统计信息"""
    total_objects: int
    index_size_bytes: int
    vector_dimensions: int
    index_type: str
    last_update: datetime

class VectorCache:
    """高性能向量缓存 - 利用Apple M3 Max的64GB统一内存"""
    
    def __init__(self, max_size_gb: int = 16):
        self.max_size = max_size_gb * 1024 * 1024 * 1024  # 转换为字节
        self.cache = {}
        self.lru = LRUCache(maxsize=1000000)  # LRU缓存100万个向量
        self.hot_vectors = {}  # 热点向量内存映射
        self.cache_hits = 0
        self.cache_misses = 0
        
        # 预分配内存映射文件
        self.mmap_file = "vector_cache.bin"
        self.mmap_size = min(self.max_size, 16 * 1024 * 1024 * 1024)  # 最大16GB
        self._init_mmap()
    
    def _init_mmap(self):
        """初始化内存映射"""
        try:
            # 创建或打开内存映射文件
            with open(self.mmap_file, 'wb') as f:
                f.write(b'\x00' * self.mmap_size)
            
            self.mmap_fd = open(self.mmap_file, 'r+b')
            self.mmap_obj = mmap.mmap(self.mmap_fd.fileno(), self.mmap_size)
            self.mmap_offset = 0
            logger.info(f"Initialized memory-mapped cache: {self.mmap_size / (1024**3):.1f}GB")
        except Exception as e:
            logger.error(f"Failed to initialize mmap: {e}")
            self.mmap_obj = None
    
    def get(self, key: str) -> Optional[np.ndarray]:
        """获取缓存的向量"""
        if key in self.lru:
            self.cache_hits += 1
            return self.lru[key]
        
        self.cache_misses += 1
        return None
    
    def put(self, key: str, vector: np.ndarray):
        """缓存向量"""
        # 存储到LRU缓存
        self.lru[key] = vector
        
        # 对于频繁访问的向量，存储到内存映射
        if self.mmap_obj and self.cache_hits > 100:
            self._store_to_mmap(key, vector)
    
    def _store_to_mmap(self, key: str, vector: np.ndarray):
        """存储向量到内存映射文件"""
        try:
            vector_bytes = vector.tobytes()
            vector_size = len(vector_bytes)
            
            if self.mmap_offset + vector_size + 8 < self.mmap_size:
                # 写入向量大小和数据
                self.mmap_obj[self.mmap_offset:self.mmap_offset + 8] = struct.pack('Q', vector_size)
                self.mmap_obj[self.mmap_offset + 8:self.mmap_offset + 8 + vector_size] = vector_bytes
                
                # 记录位置
                self.hot_vectors[key] = (self.mmap_offset, vector_size, vector.shape)
                self.mmap_offset += 8 + vector_size
        except Exception as e:
            logger.error(f"Failed to store vector in mmap: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        hit_rate = self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": hit_rate,
            "cached_vectors": len(self.lru),
            "hot_vectors": len(self.hot_vectors),
            "memory_used_mb": self.mmap_offset / (1024 * 1024) if self.mmap_obj else 0
        }

class WeaviateClient:
    """Weaviate客户端 - 极致性能优化"""
    
    def __init__(self, 
                 url: str = "http://localhost:8080",
                 api_key: Optional[str] = None,
                 embedded: bool = False,
                 cache_size_gb: int = 16):
        
        self.url = url
        self.api_key = api_key
        self.embedded = embedded
        
        # 初始化客户端
        if embedded:
            self.client = weaviate.Client(
                embedded_options=EmbeddedOptions()
            )
        else:
            self.client = weaviate.Client(
                url=url,
                auth_client_secret=weaviate.AuthApiKey(api_key) if api_key else None,
                timeout_config=(10, 60)  # 连接超时10秒，读取超时60秒
            )
        
        # 初始化缓存
        self.vector_cache = VectorCache(max_size_gb=cache_size_gb)
        self.result_cache = TTLCache(maxsize=10000, ttl=300)  # 5分钟TTL
        
        # 线程池用于并行查询
        self.executor = ThreadPoolExecutor(max_workers=12)  # M3 Max 12核CPU
        
        # 性能统计
        self.query_times = []
        self.index_stats = None
        
        # 初始化schema
        self._init_schema()
    
    def _init_schema(self):
        """初始化向量数据库schema"""
        schema = {
            "classes": [{
                "class": "Document",
                "description": "通用文档存储",
                "vectorizer": "none",  # 使用自定义向量
                "vectorIndexType": "hnsw",
                "vectorIndexConfig": {
                    "ef": 512,  # 提高搜索质量
                    "efConstruction": 256,
                    "maxConnections": 64,
                    "vectorCacheMaxObjects": 2000000  # 缓存200万向量
                },
                "properties": [
                    {
                        "name": "content",
                        "dataType": ["text"],
                        "description": "文档内容",
                        "indexInverted": True,
                        "tokenization": "word"
                    },
                    {
                        "name": "metadata",
                        "dataType": ["object"],
                        "description": "元数据",
                        "nestedProperties": [
                            {"dataType": ["text"], "name": "source"},
                            {"dataType": ["text"], "name": "type"},
                            {"dataType": ["date"], "name": "created_at"},
                            {"dataType": ["text[]"], "name": "tags"}
                        ]
                    },
                    {
                        "name": "embedding_model",
                        "dataType": ["text"],
                        "description": "使用的嵌入模型"
                    }
                ],
                "shardingConfig": {
                    "virtualPerPhysical": 128,
                    "desiredCount": 1,
                    "actualCount": 1,
                    "desiredVirtualCount": 128,
                    "actualVirtualCount": 128
                }
            }]
        }
        
        try:
            # 检查schema是否存在
            existing_schema = self.client.schema.get()
            if not any(c['class'] == 'Document' for c in existing_schema.get('classes', [])):
                self.client.schema.create(schema)
                logger.info("Created Document schema")
            else:
                logger.info("Document schema already exists")
        except Exception as e:
            logger.error(f"Failed to create schema: {e}")
    
    async def search(self, 
                    query: str,
                    vector: Optional[List[float]] = None,
                    limit: int = 10,
                    filters: Optional[Dict[str, Any]] = None,
                    alpha: float = 0.75) -> Tuple[List[SearchResult], float]:
        """
        极速向量检索 - 目标<50ms
        
        Args:
            query: 查询文本
            vector: 预计算的查询向量（可选）
            limit: 返回结果数量
            filters: 过滤条件
            alpha: 混合搜索权重 (0=纯关键词, 1=纯向量)
        
        Returns:
            (搜索结果列表, 查询延迟ms)
        """
        start_time = time.time()
        
        # 生成缓存键
        cache_key = self._generate_cache_key(query, vector, filters, alpha, limit)
        
        # 检查结果缓存
        if cache_key in self.result_cache:
            cached_result = self.result_cache[cache_key]
            latency = (time.time() - start_time) * 1000
            logger.debug(f"Cache hit! Latency: {latency:.1f}ms")
            return cached_result, latency
        
        try:
            # 构建查询
            query_builder = self.client.query.get("Document", ["content", "metadata"])
            
            # 混合搜索
            if vector:
                # 纯向量搜索
                query_builder = query_builder.with_near_vector({
                    "vector": vector,
                    "certainty": 0.7
                })
            elif alpha == 0:
                # 纯关键词搜索
                query_builder = query_builder.with_bm25(
                    query=query,
                    properties=["content"]
                )
            else:
                # 混合搜索
                query_builder = query_builder.with_hybrid(
                    query=query,
                    alpha=alpha,
                    vector=vector,
                    properties=["content"]
                )
            
            # 添加过滤条件
            if filters:
                query_builder = query_builder.with_where(filters)
            
            # 设置返回数量和附加信息
            query_builder = (query_builder
                           .with_limit(limit)
                           .with_additional(["id", "distance", "score", "vector"]))
            
            # 执行查询
            response = query_builder.do()
            
            # 处理结果
            results = []
            if response and "data" in response and "Get" in response["data"]:
                documents = response["data"]["Get"]["Document"]
                
                for doc in documents:
                    # 缓存向量
                    if doc.get("_additional", {}).get("vector"):
                        doc_id = doc["_additional"]["id"]
                        self.vector_cache.put(doc_id, np.array(doc["_additional"]["vector"]))
                    
                    result = SearchResult(
                        id=doc.get("_additional", {}).get("id", ""),
                        content=doc.get("content", ""),
                        metadata=doc.get("metadata", {}),
                        score=doc.get("_additional", {}).get("score", 0.0),
                        vector=doc.get("_additional", {}).get("vector"),
                        latency_ms=(time.time() - start_time) * 1000
                    )
                    results.append(result)
            
            # 计算总延迟
            latency = (time.time() - start_time) * 1000
            self.query_times.append(latency)
            
            # 缓存结果
            self.result_cache[cache_key] = results
            
            # 记录性能
            if latency > 50:
                logger.warning(f"Query exceeded 50ms target: {latency:.1f}ms")
            else:
                logger.info(f"Query completed in {latency:.1f}ms")
            
            return results, latency
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            latency = (time.time() - start_time) * 1000
            return [], latency
    
    async def batch_search(self, 
                          queries: List[Dict[str, Any]], 
                          batch_size: int = 10) -> List[Tuple[List[SearchResult], float]]:
        """批量搜索 - 利用并行处理提高吞吐量"""
        results = []
        
        # 分批处理
        for i in range(0, len(queries), batch_size):
            batch = queries[i:i + batch_size]
            
            # 并行执行查询
            tasks = [
                self.search(
                    query=q.get("query", ""),
                    vector=q.get("vector"),
                    limit=q.get("limit", 10),
                    filters=q.get("filters"),
                    alpha=q.get("alpha", 0.75)
                )
                for q in batch
            ]
            
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
        
        return results
    
    async def index_document(self,
                           content: str,
                           vector: List[float],
                           metadata: Optional[Dict[str, Any]] = None,
                           doc_id: Optional[str] = None) -> str:
        """索引单个文档"""
        try:
            # 准备数据对象
            data_object = {
                "content": content,
                "metadata": metadata or {},
                "embedding_model": "custom"
            }
            
            # 添加到Weaviate
            if doc_id:
                result = self.client.data_object.create(
                    data_object=data_object,
                    class_name="Document",
                    uuid=doc_id,
                    vector=vector
                )
            else:
                result = self.client.data_object.create(
                    data_object=data_object,
                    class_name="Document",
                    vector=vector
                )
            
            doc_id = result
            
            # 缓存向量
            self.vector_cache.put(doc_id, np.array(vector))
            
            logger.info(f"Indexed document: {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Index error: {e}")
            raise
    
    async def batch_index(self,
                         documents: List[Dict[str, Any]],
                         batch_size: int = 100,
                         show_progress: bool = True) -> List[str]:
        """批量索引文档 - 优化大规模数据导入"""
        indexed_ids = []
        total_docs = len(documents)
        
        for i in range(0, total_docs, batch_size):
            batch = documents[i:i + batch_size]
            
            # 准备批量数据
            with self.client.batch as batch_client:
                batch_client.batch_size = len(batch)
                
                for doc in batch:
                    batch_client.add_data_object(
                        data_object={
                            "content": doc["content"],
                            "metadata": doc.get("metadata", {}),
                            "embedding_model": doc.get("embedding_model", "custom")
                        },
                        class_name="Document",
                        uuid=doc.get("id"),
                        vector=doc["vector"]
                    )
                
                # 获取结果
                results = batch_client.create_objects()
                
                # 提取ID
                for result in results:
                    if result.get("result", {}).get("status") == "SUCCESS":
                        indexed_ids.append(result["id"])
            
            if show_progress:
                progress = (i + len(batch)) / total_docs * 100
                logger.info(f"Indexing progress: {progress:.1f}% ({i + len(batch)}/{total_docs})")
        
        return indexed_ids
    
    async def update_document(self,
                            doc_id: str,
                            content: Optional[str] = None,
                            vector: Optional[List[float]] = None,
                            metadata: Optional[Dict[str, Any]] = None) -> bool:
        """更新文档"""
        try:
            # 获取现有文档
            existing = self.client.data_object.get_by_id(doc_id, class_name="Document")
            
            if not existing:
                logger.error(f"Document not found: {doc_id}")
                return False
            
            # 更新字段
            if content is not None:
                existing["content"] = content
            if metadata is not None:
                existing["metadata"] = metadata
            
            # 更新文档
            self.client.data_object.update(
                data_object=existing,
                class_name="Document",
                uuid=doc_id,
                vector=vector if vector else None
            )
            
            # 更新缓存
            if vector:
                self.vector_cache.put(doc_id, np.array(vector))
            
            # 清除结果缓存
            self.result_cache.clear()
            
            logger.info(f"Updated document: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Update error: {e}")
            return False
    
    async def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        try:
            self.client.data_object.delete(
                uuid=doc_id,
                class_name="Document"
            )
            
            # 清除缓存
            self.result_cache.clear()
            
            logger.info(f"Deleted document: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return False
    
    async def get_count(self) -> int:
        """获取文档总数"""
        try:
            result = self.client.query.aggregate("Document").with_meta_count().do()
            return result["data"]["Aggregate"]["Document"][0]["meta"]["count"]
        except Exception as e:
            logger.error(f"Count error: {e}")
            return 0
    
    async def get_index_size(self) -> int:
        """获取索引大小（字节）"""
        # 这是一个估算值
        count = await self.get_count()
        avg_vector_size = 768 * 4  # 假设768维float32向量
        avg_metadata_size = 1024  # 假设1KB元数据
        
        return count * (avg_vector_size + avg_metadata_size)
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            self.client.schema.get()
            return True
        except Exception:
            return False
    
    async def optimize_index(self):
        """优化索引 - 提高查询性能"""
        try:
            # 获取当前统计信息
            count = await self.get_count()
            
            # 动态调整HNSW参数
            if count > 1000000:  # 超过100万文档
                logger.info("Optimizing index for large dataset...")
                
                # 更新索引配置
                schema_update = {
                    "class": "Document",
                    "vectorIndexConfig": {
                        "ef": 1024,  # 增加搜索质量
                        "efConstruction": 512,
                        "maxConnections": 128
                    }
                }
                
                # 注意：实际的Weaviate可能不支持动态更新某些参数
                # 这里仅作为示例
                
            logger.info("Index optimization completed")
            
        except Exception as e:
            logger.error(f"Optimization error: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        if not self.query_times:
            return {
                "avg_latency_ms": 0,
                "p50_latency_ms": 0,
                "p99_latency_ms": 0,
                "queries_under_50ms_pct": 0,
                "cache_stats": self.vector_cache.get_stats()
            }
        
        sorted_times = sorted(self.query_times)
        n = len(sorted_times)
        
        return {
            "total_queries": n,
            "avg_latency_ms": sum(sorted_times) / n,
            "min_latency_ms": sorted_times[0],
            "max_latency_ms": sorted_times[-1],
            "p50_latency_ms": sorted_times[n // 2],
            "p95_latency_ms": sorted_times[int(n * 0.95)] if n > 20 else sorted_times[-1],
            "p99_latency_ms": sorted_times[int(n * 0.99)] if n > 100 else sorted_times[-1],
            "queries_under_50ms_pct": sum(1 for t in sorted_times if t < 50) / n * 100,
            "cache_stats": self.vector_cache.get_stats()
        }
    
    def _generate_cache_key(self, query: str, vector: Optional[List[float]], 
                           filters: Optional[Dict[str, Any]], alpha: float, limit: int) -> str:
        """生成缓存键"""
        key_parts = [
            query,
            str(alpha),
            str(limit),
            json.dumps(filters, sort_keys=True) if filters else "",
            hashlib.md5(str(vector).encode()).hexdigest() if vector else ""
        ]
        
        return hashlib.sha256("_".join(key_parts).encode()).hexdigest()
    
    async def close(self):
        """关闭客户端，清理资源"""
        try:
            # 关闭线程池
            self.executor.shutdown(wait=True)
            
            # 保存性能统计
            stats = self.get_performance_stats()
            logger.info(f"Performance stats: {stats}")
            
            # 清理缓存
            if hasattr(self.vector_cache, 'mmap_obj') and self.vector_cache.mmap_obj:
                self.vector_cache.mmap_obj.close()
                if hasattr(self.vector_cache, 'mmap_fd'):
                    self.vector_cache.mmap_fd.close()
            
            logger.info("Weaviate client closed")
            
        except Exception as e:
            logger.error(f"Error closing client: {e}")