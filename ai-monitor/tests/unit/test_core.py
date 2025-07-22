"""
核心引擎单元测试
"""
import pytest
import time
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio

from core.main import (
    AIMonitorCore, 
    LLMRequest, 
    VectorRequest,
    Settings,
    HealthResponse,
    SystemMetrics
)


class TestAIMonitorCore:
    """AI监理系统核心引擎测试"""

    @pytest.mark.unit
    def test_core_initialization(self):
        """测试核心引擎初始化"""
        core = AIMonitorCore()
        
        assert core.start_time > 0
        assert core.redis_client is None
        assert core.db_pool is None
        assert core.ollama_client is None
        assert core.weaviate_client is None
        assert core.active_connections == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_core_initialize_success(self):
        """测试核心引擎成功初始化"""
        core = AIMonitorCore()
        
        with patch('aioredis.from_url') as mock_redis, \
             patch('asyncpg.create_pool') as mock_db, \
             patch('httpx.AsyncClient') as mock_http:
            
            # 配置mocks
            mock_redis_client = AsyncMock()
            mock_redis_client.ping.return_value = True
            mock_redis.return_value = mock_redis_client
            
            mock_db_pool = AsyncMock()
            mock_db.return_value = mock_db_pool
            
            mock_http_client = AsyncMock()
            mock_http.return_value = mock_http_client
            
            # 执行初始化
            await core.initialize()
            
            # 验证初始化结果
            assert core.redis_client == mock_redis_client
            assert core.db_pool == mock_db_pool
            assert core.ollama_client is not None
            assert core.weaviate_client is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_core_initialize_with_failures(self):
        """测试核心引擎初始化时的失败处理"""
        core = AIMonitorCore()
        
        with patch('aioredis.from_url', side_effect=Exception("Redis连接失败")), \
             patch('asyncpg.create_pool', side_effect=Exception("数据库连接失败")), \
             patch('httpx.AsyncClient') as mock_http:
            
            mock_http_client = AsyncMock()
            mock_http.return_value = mock_http_client
            
            # 执行初始化（应该不抛出异常）
            await core.initialize()
            
            # 验证失败的组件为None
            assert core.redis_client is None
            assert core.db_pool is None
            assert core.ollama_client is not None
            assert core.weaviate_client is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_core_cleanup(self):
        """测试核心引擎资源清理"""
        core = AIMonitorCore()
        
        # 设置mock客户端
        core.redis_client = AsyncMock()
        core.db_pool = AsyncMock()
        core.ollama_client = AsyncMock()
        core.weaviate_client = AsyncMock()
        
        # 执行清理
        await core.cleanup()
        
        # 验证清理调用
        core.redis_client.close.assert_called_once()
        core.db_pool.close.assert_called_once()
        core.ollama_client.aclose.assert_called_once()
        core.weaviate_client.aclose.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_llm_request_success(self, sample_llm_request):
        """测试成功处理LLM请求"""
        core = AIMonitorCore()
        
        # 设置mock Ollama客户端
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "测试响应内容",
            "prompt_eval_count": 10,
            "eval_count": 50
        }
        
        core.ollama_client = AsyncMock()
        core.ollama_client.post.return_value = mock_response
        
        # 执行请求
        result = await core.process_llm_request(sample_llm_request)
        
        # 验证结果
        assert result.response == "测试响应内容"
        assert result.model == sample_llm_request.model
        assert result.tokens_used == 60  # 10 + 50
        assert result.processing_time > 0
        assert result.timestamp > 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_llm_request_failure(self, sample_llm_request):
        """测试LLM请求失败处理"""
        core = AIMonitorCore()
        
        # 设置mock失败响应
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.text = "内部服务器错误"
        
        core.ollama_client = AsyncMock()
        core.ollama_client.post.return_value = mock_response
        
        # 验证抛出异常
        with pytest.raises(Exception):
            await core.process_llm_request(sample_llm_request)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_vector_request_success(self, sample_vector_request):
        """测试成功处理向量化请求"""
        core = AIMonitorCore()
        
        # 设置mock响应
        embedding_data = [0.1, 0.2, 0.3] * 256  # 768维向量
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embedding": embedding_data
        }
        
        core.ollama_client = AsyncMock()
        core.ollama_client.post.return_value = mock_response
        
        # 设置mock Redis（可选）
        core.redis_client = AsyncMock()
        
        # 执行请求
        result = await core.process_vector_request(sample_vector_request)
        
        # 验证结果
        assert result.embedding == embedding_data
        assert result.dimension == len(embedding_data)
        assert result.text == sample_vector_request.text
        assert result.collection == sample_vector_request.collection
        assert result.timestamp > 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_vector_request_with_cache(self, sample_vector_request):
        """测试向量化请求的缓存功能"""
        core = AIMonitorCore()
        
        # 设置mock响应
        embedding_data = [0.1] * 768
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embedding": embedding_data
        }
        
        core.ollama_client = AsyncMock()
        core.ollama_client.post.return_value = mock_response
        
        # 设置mock Redis
        core.redis_client = AsyncMock()
        
        # 执行请求
        result = await core.process_vector_request(sample_vector_request)
        
        # 验证缓存调用
        core.redis_client.setex.assert_called_once()
        cache_call = core.redis_client.setex.call_args
        assert cache_call[0][1] == 3600  # 缓存1小时

    @pytest.mark.unit
    def test_get_system_metrics(self):
        """测试获取系统指标"""
        core = AIMonitorCore()
        
        with patch('psutil.cpu_percent', return_value=25.5), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk, \
             patch('psutil.net_io_counters') as mock_network, \
             patch('os.getloadavg', return_value=[1.0, 1.5, 2.0]):
            
            # 配置mock返回值
            mock_memory.return_value = MagicMock(
                percent=45.2,
                used=8 * 1024 * 1024 * 1024,  # 8GB
                total=16 * 1024 * 1024 * 1024  # 16GB
            )
            
            mock_disk.return_value = MagicMock(
                total=1000 * 1024 * 1024 * 1024,  # 1TB
                used=500 * 1024 * 1024 * 1024,    # 500GB
                free=500 * 1024 * 1024 * 1024,    # 500GB
                percent=50.0
            )
            
            mock_network.return_value = MagicMock(
                bytes_sent=1024 * 1024,
                bytes_recv=2 * 1024 * 1024,
                packets_sent=1000,
                packets_recv=2000
            )
            
            # 执行获取指标
            metrics = core.get_system_metrics()
            
            # 验证结果
            assert isinstance(metrics, SystemMetrics)
            assert metrics.cpu_percent == 25.5
            assert metrics.memory_percent == 45.2
            assert metrics.memory_used == 8 * 1024 * 1024 * 1024
            assert metrics.memory_total == 16 * 1024 * 1024 * 1024
            assert metrics.disk_usage["percent"] == 50.0
            assert metrics.load_average == [1.0, 1.5, 2.0]
            assert metrics.timestamp > 0


class TestSettings:
    """配置类测试"""

    @pytest.mark.unit
    def test_default_settings(self):
        """测试默认配置"""
        settings = Settings()
        
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
        assert settings.debug is True
        assert settings.max_workers == 12
        assert "localhost" in settings.ollama_url
        assert "localhost" in settings.weaviate_url

    @pytest.mark.unit
    def test_custom_settings(self):
        """测试自定义配置"""
        with patch.dict('os.environ', {
            'HOST': '127.0.0.1',
            'PORT': '9000',
            'DEBUG': 'false',
            'MAX_WORKERS': '8'
        }):
            settings = Settings()
            
            assert settings.host == "127.0.0.1"
            assert settings.port == 9000
            assert settings.debug is False
            assert settings.max_workers == 8


class TestDataModels:
    """数据模型测试"""

    @pytest.mark.unit
    def test_llm_request_validation(self):
        """测试LLM请求模型验证"""
        # 有效请求
        valid_request = LLMRequest(
            model="llama3.2",
            prompt="测试提示词",
            temperature=0.8,
            max_tokens=512
        )
        assert valid_request.model == "llama3.2"
        assert valid_request.temperature == 0.8
        
        # 无效温度
        with pytest.raises(ValueError):
            LLMRequest(
                model="llama3.2",
                prompt="测试",
                temperature=3.0  # 超出范围
            )
        
        # 无效最大令牌数
        with pytest.raises(ValueError):
            LLMRequest(
                model="llama3.2",
                prompt="测试",
                max_tokens=0  # 小于最小值
            )

    @pytest.mark.unit
    def test_vector_request_validation(self):
        """测试向量请求模型验证"""
        # 有效请求
        valid_request = VectorRequest(
            text="测试文本",
            collection="test_collection"
        )
        assert valid_request.text == "测试文本"
        assert valid_request.collection == "test_collection"
        
        # 空文本（应该失败）
        with pytest.raises(ValueError):
            VectorRequest(text="")

    @pytest.mark.unit
    def test_health_response_model(self):
        """测试健康检查响应模型"""
        response = HealthResponse(
            status="healthy",
            timestamp=int(time.time()),
            version="2.1.0",
            uptime=3600,
            system={
                "cpu_percent": 25.0,
                "memory_percent": 45.0
            }
        )
        
        assert response.status == "healthy"
        assert response.version == "2.1.0"
        assert response.uptime == 3600
        assert "cpu_percent" in response.system