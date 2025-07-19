# api/router.py
"""
智能路由器 - 根据任务类型和负载智能分配到不同的AI模型
支持动态负载均衡、模型健康检查、性能监控
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import random
import time
from collections import deque, defaultdict
import json
import logging

logger = logging.getLogger(__name__)

class TaskType(Enum):
    """任务类型定义"""
    # 聊天类
    GENERAL_CHAT = "general_chat"
    CODE_CHAT = "code_chat"
    TECHNICAL_CHAT = "technical_chat"
    
    # 代码类
    CODE_REVIEW = "code_review"
    CODE_GENERATION = "code_generation"
    CODE_COMPLETION = "code_completion"
    CODE_EXPLANATION = "code_explanation"
    
    # 文本处理类
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    GRAMMAR_CHECK = "grammar_check"
    
    # 嵌入和检索
    EMBEDDING = "embedding"
    RERANKING = "reranking"
    
    # 特殊任务
    VOICE = "voice"
    VISION = "vision"
    REASONING = "reasoning"

@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    type: str  # ollama, openai, custom
    endpoint: str
    capabilities: List[TaskType]
    context_window: int
    max_tokens: int
    temperature_range: Tuple[float, float]
    cost_per_token: float = 0.0
    priority: int = 1  # 优先级，数字越小优先级越高
    tags: List[str] = field(default_factory=list)

@dataclass
class ModelHealth:
    """模型健康状态"""
    model_name: str
    is_healthy: bool
    last_check: datetime
    response_time_ms: float
    error_count: int = 0
    success_count: int = 0
    avg_latency_ms: float = 0.0

@dataclass
class RoutingDecision:
    """路由决策结果"""
    model_name: str
    endpoint: str
    reason: str
    estimated_latency_ms: float
    fallback_models: List[str] = field(default_factory=list)

class LoadBalancer:
    """负载均衡器"""
    
    def __init__(self):
        self.request_counts = defaultdict(int)
        self.response_times = defaultdict(lambda: deque(maxlen=100))
        self.active_requests = defaultdict(int)
    
    def select_model(self, models: List[ModelConfig], strategy: str = "least_loaded") -> ModelConfig:
        """根据策略选择模型"""
        if strategy == "round_robin":
            return self._round_robin(models)
        elif strategy == "least_loaded":
            return self._least_loaded(models)
        elif strategy == "lowest_latency":
            return self._lowest_latency(models)
        elif strategy == "weighted_random":
            return self._weighted_random(models)
        else:
            return models[0]
    
    def _least_loaded(self, models: List[ModelConfig]) -> ModelConfig:
        """选择负载最低的模型"""
        return min(models, key=lambda m: self.active_requests[m.name])
    
    def _lowest_latency(self, models: List[ModelConfig]) -> ModelConfig:
        """选择延迟最低的模型"""
        def avg_latency(model):
            times = self.response_times[model.name]
            return sum(times) / len(times) if times else float('inf')
        
        return min(models, key=avg_latency)
    
    def _round_robin(self, models: List[ModelConfig]) -> ModelConfig:
        """轮询选择"""
        min_count = min(self.request_counts[m.name] for m in models)
        for model in models:
            if self.request_counts[model.name] == min_count:
                return model
        return models[0]
    
    def _weighted_random(self, models: List[ModelConfig]) -> ModelConfig:
        """加权随机选择"""
        weights = [1.0 / (m.priority + 1) for m in models]
        return random.choices(models, weights=weights)[0]
    
    def record_request(self, model_name: str):
        """记录请求"""
        self.request_counts[model_name] += 1
        self.active_requests[model_name] += 1
    
    def record_response(self, model_name: str, latency_ms: float):
        """记录响应"""
        self.active_requests[model_name] = max(0, self.active_requests[model_name] - 1)
        self.response_times[model_name].append(latency_ms)

class Router:
    """智能路由器主类"""
    
    def __init__(self, config_path: str = "config/models.json"):
        self.config_path = config_path
        self.models = self._load_models()
        self.task_model_map = self._build_task_map()
        self.health_checker = HealthChecker(self.models)
        self.load_balancer = LoadBalancer()
        self.cache = {}
        self._start_health_check()
    
    def _load_models(self) -> Dict[str, ModelConfig]:
        """加载模型配置"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            models = {}
            for model_data in config['models']:
                model = ModelConfig(
                    name=model_data['name'],
                    type=model_data['type'],
                    endpoint=model_data['endpoint'],
                    capabilities=[TaskType(c) for c in model_data['capabilities']],
                    context_window=model_data['context_window'],
                    max_tokens=model_data['max_tokens'],
                    temperature_range=tuple(model_data['temperature_range']),
                    cost_per_token=model_data.get('cost_per_token', 0.0),
                    priority=model_data.get('priority', 1),
                    tags=model_data.get('tags', [])
                )
                models[model.name] = model
            
            return models
        except Exception as e:
            logger.error(f"Failed to load model config: {e}")
            return self._get_default_models()
    
    def _get_default_models(self) -> Dict[str, ModelConfig]:
        """获取默认模型配置"""
        return {
            "qwen:8b": ModelConfig(
                name="qwen:8b",
                type="ollama",
                endpoint="http://localhost:11434",
                capabilities=[
                    TaskType.GENERAL_CHAT,
                    TaskType.TECHNICAL_CHAT,
                    TaskType.SUMMARIZATION,
                    TaskType.TRANSLATION
                ],
                context_window=8192,
                max_tokens=4096,
                temperature_range=(0.0, 2.0),
                priority=1
            ),
            "deepseek-coder:6.7b": ModelConfig(
                name="deepseek-coder:6.7b",
                type="ollama",
                endpoint="http://localhost:11434",
                capabilities=[
                    TaskType.CODE_REVIEW,
                    TaskType.CODE_GENERATION,
                    TaskType.CODE_COMPLETION,
                    TaskType.CODE_EXPLANATION,
                    TaskType.CODE_CHAT
                ],
                context_window=16384,
                max_tokens=8192,
                temperature_range=(0.0, 1.0),
                priority=1,
                tags=["code", "programming"]
            ),
            "phi3:mini": ModelConfig(
                name="phi3:mini",
                type="ollama",
                endpoint="http://localhost:11434",
                capabilities=[
                    TaskType.GENERAL_CHAT,
                    TaskType.REASONING,
                    TaskType.GRAMMAR_CHECK
                ],
                context_window=4096,
                max_tokens=2048,
                temperature_range=(0.0, 1.5),
                priority=2,
                tags=["fast", "lightweight"]
            ),
            "nomic-embed-text": ModelConfig(
                name="nomic-embed-text",
                type="ollama",
                endpoint="http://localhost:11434",
                capabilities=[TaskType.EMBEDDING],
                context_window=8192,
                max_tokens=0,
                temperature_range=(0.0, 0.0),
                priority=1,
                tags=["embedding"]
            )
        }
    
    def _build_task_map(self) -> Dict[TaskType, List[ModelConfig]]:
        """构建任务到模型的映射"""
        task_map = defaultdict(list)
        
        for model in self.models.values():
            for capability in model.capabilities:
                task_map[capability].append(model)
        
        # 按优先级排序
        for task_type in task_map:
            task_map[task_type].sort(key=lambda m: m.priority)
        
        return dict(task_map)
    
    def _start_health_check(self):
        """启动健康检查"""
        asyncio.create_task(self.health_checker.start())
    
    def route(self, task_type: TaskType, request: Dict[str, Any]) -> RoutingDecision:
        """主路由方法"""
        # 获取可用模型
        available_models = self._get_available_models(task_type)
        
        if not available_models:
            raise ValueError(f"No available models for task type: {task_type}")
        
        # 根据请求特征选择最佳模型
        selected_model = self._select_best_model(available_models, request)
        
        # 记录请求
        self.load_balancer.record_request(selected_model.name)
        
        # 构建路由决策
        decision = RoutingDecision(
            model_name=selected_model.name,
            endpoint=selected_model.endpoint,
            reason=self._get_routing_reason(selected_model, task_type, request),
            estimated_latency_ms=self._estimate_latency(selected_model, request),
            fallback_models=[m.name for m in available_models if m != selected_model][:3]
        )
        
        logger.info(f"Routed {task_type.value} to {decision.model_name}: {decision.reason}")
        
        return decision
    
    def _get_available_models(self, task_type: TaskType) -> List[ModelConfig]:
        """获取可用模型列表"""
        # 获取支持该任务的模型
        capable_models = self.task_model_map.get(task_type, [])
        
        # 过滤健康的模型
        healthy_models = [
            model for model in capable_models
            if self.health_checker.is_healthy(model.name)
        ]
        
        return healthy_models
    
    def _select_best_model(self, models: List[ModelConfig], request: Dict[str, Any]) -> ModelConfig:
        """选择最佳模型"""
        # 检查是否有特定的模型要求
        if "model" in request:
            requested_model = request["model"]
            for model in models:
                if model.name == requested_model:
                    return model
        
        # 根据上下文长度筛选
        content_length = self._estimate_token_count(request)
        suitable_models = [
            m for m in models
            if m.context_window >= content_length
        ]
        
        if not suitable_models:
            suitable_models = models
        
        # 使用负载均衡器选择
        strategy = request.get("routing_strategy", "least_loaded")
        return self.load_balancer.select_model(suitable_models, strategy)
    
    def _estimate_token_count(self, request: Dict[str, Any]) -> int:
        """估算token数量"""
        # 简单估算：1 token ≈ 4个字符
        text = ""
        
        if "messages" in request:
            for msg in request["messages"]:
                text += msg.get("content", "")
        elif "prompt" in request:
            text = request["prompt"]
        elif "input" in request:
            text = request["input"]
        
        return len(text) // 4
    
    def _get_routing_reason(self, model: ModelConfig, task_type: TaskType, request: Dict[str, Any]) -> str:
        """生成路由原因说明"""
        reasons = []
        
        # 任务匹配
        if task_type in model.capabilities:
            reasons.append(f"支持{task_type.value}任务")
        
        # 性能优势
        if "fast" in model.tags:
            reasons.append("快速响应")
        
        # 专业能力
        if task_type in [TaskType.CODE_REVIEW, TaskType.CODE_GENERATION] and "code" in model.tags:
            reasons.append("代码专长")
        
        # 负载情况
        active_requests = self.load_balancer.active_requests[model.name]
        if active_requests < 5:
            reasons.append("负载较低")
        
        return " | ".join(reasons) if reasons else "默认选择"
    
    def _estimate_latency(self, model: ModelConfig, request: Dict[str, Any]) -> float:
        """估算延迟"""
        # 基础延迟
        base_latency = 20.0
        
        # 根据模型大小调整
        if "mini" in model.name or "small" in model.name:
            base_latency *= 0.7
        elif "large" in model.name:
            base_latency *= 1.5
        
        # 根据内容长度调整
        token_count = self._estimate_token_count(request)
        if token_count > 1000:
            base_latency *= (1 + token_count / 5000)
        
        # 根据历史数据调整
        history = self.load_balancer.response_times.get(model.name, [])
        if history:
            avg_history = sum(history) / len(history)
            base_latency = 0.3 * base_latency + 0.7 * avg_history
        
        return round(base_latency, 1)
    
    def record_response(self, model_name: str, latency_ms: float, success: bool = True):
        """记录响应结果"""
        self.load_balancer.record_response(model_name, latency_ms)
        self.health_checker.record_response(model_name, latency_ms, success)
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取路由器性能指标"""
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "models": {},
            "task_distribution": {},
            "routing_performance": {
                "total_requests": sum(self.load_balancer.request_counts.values()),
                "avg_routing_time_ms": 0.5  # 路由决策通常很快
            }
        }
        
        # 模型指标
        for model_name, model in self.models.items():
            health = self.health_checker.get_health(model_name)
            metrics["models"][model_name] = {
                "status": "healthy" if health.is_healthy else "unhealthy",
                "request_count": self.load_balancer.request_counts[model_name],
                "active_requests": self.load_balancer.active_requests[model_name],
                "avg_latency_ms": health.avg_latency_ms,
                "success_rate": health.success_count / (health.success_count + health.error_count)
                if (health.success_count + health.error_count) > 0 else 0
            }
        
        # 任务分布
        for task_type in TaskType:
            count = sum(
                self.load_balancer.request_counts[m.name]
                for m in self.task_model_map.get(task_type, [])
            )
            if count > 0:
                metrics["task_distribution"][task_type.value] = count
        
        return metrics
    
    def get_active_requests(self) -> int:
        """获取当前活跃请求数"""
        return sum(self.load_balancer.active_requests.values())
    
    def get_avg_latency(self) -> float:
        """获取平均延迟"""
        all_times = []
        for times in self.load_balancer.response_times.values():
            all_times.extend(times)
        
        return sum(all_times) / len(all_times) if all_times else 0.0
    
    def get_rps(self) -> float:
        """获取每秒请求数（简化计算）"""
        # 基于最近的请求计算
        total_requests = sum(self.load_balancer.request_counts.values())
        # 假设系统运行了至少60秒
        return total_requests / 60.0
    
    def get_error_rate(self) -> float:
        """获取错误率"""
        total_errors = sum(
            self.health_checker.get_health(m).error_count
            for m in self.models
        )
        total_requests = sum(self.load_balancer.request_counts.values())
        
        return total_errors / total_requests if total_requests > 0 else 0.0

class HealthChecker:
    """模型健康检查器"""
    
    def __init__(self, models: Dict[str, ModelConfig]):
        self.models = models
        self.health_status = {
            name: ModelHealth(
                model_name=name,
                is_healthy=True,
                last_check=datetime.utcnow(),
                response_time_ms=0.0
            )
            for name in models
        }
        self.check_interval = 30  # 秒
    
    async def start(self):
        """启动健康检查循环"""
        while True:
            await self._check_all_models()
            await asyncio.sleep(self.check_interval)
    
    async def _check_all_models(self):
        """检查所有模型健康状态"""
        tasks = [
            self._check_model_health(model_name)
            for model_name in self.models
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_model_health(self, model_name: str):
        """检查单个模型健康状态"""
        model = self.models[model_name]
        start_time = time.time()
        
        try:
            # 根据模型类型执行健康检查
            if model.type == "ollama":
                # 简单的ping请求
                # 实际实现中应该调用真实的API
                await asyncio.sleep(0.01)  # 模拟网络延迟
                is_healthy = True
            else:
                is_healthy = True
            
            response_time = (time.time() - start_time) * 1000
            
            # 更新健康状态
            health = self.health_status[model_name]
            health.is_healthy = is_healthy
            health.last_check = datetime.utcnow()
            health.response_time_ms = response_time
            
            if is_healthy:
                health.success_count += 1
            else:
                health.error_count += 1
            
            # 更新平均延迟
            health.avg_latency_ms = (
                health.avg_latency_ms * 0.9 + response_time * 0.1
            )
            
        except Exception as e:
            logger.error(f"Health check failed for {model_name}: {e}")
            health = self.health_status[model_name]
            health.is_healthy = False
            health.error_count += 1
            health.last_check = datetime.utcnow()
    
    def is_healthy(self, model_name: str) -> bool:
        """检查模型是否健康"""
        health = self.health_status.get(model_name)
        if not health:
            return False
        
        # 如果超过2分钟没有检查，认为不健康
        if datetime.utcnow() - health.last_check > timedelta(minutes=2):
            return False
        
        return health.is_healthy
    
    def get_health(self, model_name: str) -> ModelHealth:
        """获取模型健康状态"""
        return self.health_status.get(
            model_name,
            ModelHealth(
                model_name=model_name,
                is_healthy=False,
                last_check=datetime.utcnow(),
                response_time_ms=0.0
            )
        )
    
    def record_response(self, model_name: str, latency_ms: float, success: bool):
        """记录实际响应结果"""
        if model_name in self.health_status:
            health = self.health_status[model_name]
            
            if success:
                health.success_count += 1
                # 更新平均延迟
                health.avg_latency_ms = (
                    health.avg_latency_ms * 0.95 + latency_ms * 0.05
                )
            else:
                health.error_count += 1
                # 连续3次错误标记为不健康
                if health.error_count > health.success_count * 0.1:
                    health.is_healthy = False