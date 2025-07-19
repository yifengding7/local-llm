"""
测试配置和Fixtures
"""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock
import httpx
from fastapi.testclient import TestClient

# 导入待测试的模块
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.main import app, core, settings


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """FastAPI测试客户端"""
    with TestClient(app) as c:
        yield c


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """异步HTTP客户端"""
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_ollama():
    """Mock Ollama客户端"""
    mock = AsyncMock()
    
    # 模拟生成响应
    mock.post.return_value.status_code = 200
    mock.post.return_value.json.return_value = {
        "response": "测试响应",
        "prompt_eval_count": 10,
        "eval_count": 50
    }
    
    # 模拟向量化响应
    mock.post.return_value.json.return_value = {
        "embedding": [0.1] * 768
    }
    
    return mock


@pytest.fixture
def mock_weaviate():
    """Mock Weaviate客户端"""
    mock = AsyncMock()
    mock.get.return_value.status_code = 200
    mock.get.return_value.json.return_value = {"status": "ok"}
    return mock


@pytest.fixture
def mock_redis():
    """Mock Redis客户端"""
    mock = AsyncMock()
    mock.ping.return_value = True
    mock.setex.return_value = True
    mock.get.return_value = None
    return mock


@pytest.fixture
def mock_db_pool():
    """Mock 数据库连接池"""
    mock = AsyncMock()
    mock.acquire.return_value.__aenter__.return_value = AsyncMock()
    return mock


@pytest_asyncio.fixture
async def initialized_core(mock_ollama, mock_weaviate, mock_redis, mock_db_pool):
    """初始化的核心引擎（使用mock）"""
    # 替换真实客户端为mock
    original_ollama = core.ollama_client
    original_weaviate = core.weaviate_client
    original_redis = core.redis_client
    original_db = core.db_pool
    
    core.ollama_client = mock_ollama
    core.weaviate_client = mock_weaviate
    core.redis_client = mock_redis
    core.db_pool = mock_db_pool
    
    yield core
    
    # 恢复原始客户端
    core.ollama_client = original_ollama
    core.weaviate_client = original_weaviate
    core.redis_client = original_redis
    core.db_pool = original_db


@pytest.fixture
def sample_llm_request():
    """示例LLM请求"""
    from core.main import LLMRequest
    return LLMRequest(
        model="llama3.2",
        prompt="Hello, world!",
        temperature=0.7,
        max_tokens=100
    )


@pytest.fixture
def sample_vector_request():
    """示例向量化请求"""
    from core.main import VectorRequest
    return VectorRequest(
        text="测试文本向量化",
        collection="test"
    )


@pytest.fixture(autouse=True)
def reset_metrics():
    """重置Prometheus指标"""
    from core.main import REQUEST_COUNT, REQUEST_DURATION, ACTIVE_CONNECTIONS, MEMORY_USAGE, CPU_USAGE
    
    # 清除计数器（注意：实际使用中应避免重置生产指标）
    REQUEST_COUNT._value._value = 0
    ACTIVE_CONNECTIONS.set(0)
    
    yield
    
    # 测试后清理
    ACTIVE_CONNECTIONS.set(0)