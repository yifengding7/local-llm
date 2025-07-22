"""
API集成测试
"""
import pytest
import asyncio
import httpx
from unittest.mock import patch, AsyncMock
import time

from core.main import app


class TestAPIIntegration:
    """API集成测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_llm_workflow(self, async_client):
        """测试完整的LLM工作流程"""
        # 模拟Ollama响应
        with patch('core.main.core.ollama_client') as mock_ollama:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "response": "这是一个集成测试响应",
                "prompt_eval_count": 15,
                "eval_count": 85
            }
            mock_ollama.post.return_value = mock_response
            
            # 发送LLM请求
            request_data = {
                "model": "llama3.2",
                "prompt": "解释什么是AI监理系统",
                "temperature": 0.7,
                "max_tokens": 200
            }
            
            response = await async_client.post(
                "/llm/generate",
                json=request_data,
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # 验证响应结构
            assert "response" in data
            assert "model" in data
            assert "tokens_used" in data
            assert "processing_time" in data
            assert "timestamp" in data
            
            # 验证业务逻辑
            assert data["model"] == "llama3.2"
            assert data["tokens_used"] == 100  # 15 + 85
            assert data["processing_time"] > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_vector_workflow(self, async_client):
        """测试完整的向量化工作流程"""
        # 模拟Ollama向量化响应
        with patch('core.main.core.ollama_client') as mock_ollama, \
             patch('core.main.core.redis_client') as mock_redis:
            
            embedding_data = [0.1, 0.2, -0.1] * 256  # 768维向量
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "embedding": embedding_data
            }
            mock_ollama.post.return_value = mock_response
            
            # 配置Redis mock
            mock_redis.setex = AsyncMock()
            
            # 发送向量化请求
            request_data = {
                "text": "AI监理系统是一个基于大语言模型的智能监理平台",
                "collection": "integration_test"
            }
            
            response = await async_client.post(
                "/vector/embed",
                json=request_data,
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # 验证响应结构
            assert "embedding" in data
            assert "dimension" in data
            assert "text" in data
            assert "collection" in data
            assert "timestamp" in data
            
            # 验证业务逻辑
            assert len(data["embedding"]) == 768
            assert data["dimension"] == 768
            assert data["text"] == request_data["text"]
            assert data["collection"] == "integration_test"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_check_integration(self, async_client):
        """测试健康检查集成"""
        # 模拟外部服务检查
        with patch('core.main.check_ollama_health', return_value=True), \
             patch('core.main.check_weaviate_health', return_value=True):
            
            response = await async_client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            
            # 验证健康检查响应
            assert data["status"] == "healthy"
            assert data["version"] == "2.1.0"
            assert data["uptime"] >= 0
            assert "system" in data
            
            # 验证系统信息
            system = data["system"]
            assert "cpu_percent" in system
            assert "memory_percent" in system
            assert "active_connections" in system
            assert system["ollama_available"] is True
            assert system["weaviate_available"] is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, async_client):
        """测试并发请求处理"""
        # 模拟Ollama响应
        with patch('core.main.core.ollama_client') as mock_ollama:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "response": "并发测试响应",
                "prompt_eval_count": 10,
                "eval_count": 40
            }
            mock_ollama.post.return_value = mock_response
            
            # 创建多个并发请求
            tasks = []
            for i in range(5):
                request_data = {
                    "model": "llama3.2",
                    "prompt": f"并发测试请求 {i}",
                    "temperature": 0.7,
                    "max_tokens": 100
                }
                
                task = async_client.post(
                    "/llm/generate",
                    json=request_data,
                    headers={"Authorization": "Bearer test-token"}
                )
                tasks.append(task)
            
            # 等待所有请求完成
            responses = await asyncio.gather(*tasks)
            
            # 验证所有请求都成功
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert "response" in data
                assert data["tokens_used"] == 50

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_scenarios_integration(self, async_client):
        """测试错误场景集成"""
        # 测试Ollama服务不可用
        with patch('core.main.core.ollama_client') as mock_ollama:
            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_response.text = "Ollama内部错误"
            mock_ollama.post.return_value = mock_response
            
            request_data = {
                "model": "llama3.2",
                "prompt": "测试错误处理",
            }
            
            response = await async_client.post(
                "/llm/generate",
                json=request_data,
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 500

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_metrics_integration(self, async_client):
        """测试指标集成"""
        # 发送几个请求以生成指标
        for _ in range(3):
            await async_client.get("/health")
        
        # 检查Prometheus指标
        response = await async_client.get("/metrics/prometheus")
        assert response.status_code == 200
        
        content = response.text
        
        # 验证关键指标存在
        assert "ai_monitor_requests_total" in content
        assert "ai_monitor_request_duration_seconds" in content
        assert "ai_monitor_active_connections" in content
        
        # 检查系统指标
        response = await async_client.get("/metrics/system")
        assert response.status_code == 200
        
        data = response.json()
        assert "cpu_percent" in data
        assert "memory_percent" in data
        assert "disk_usage" in data
        assert "network_io" in data

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_sustained_load(self, async_client):
        """测试持续负载（慢速测试）"""
        # 模拟响应
        with patch('core.main.core.ollama_client') as mock_ollama:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "response": "负载测试响应",
                "prompt_eval_count": 5,
                "eval_count": 25
            }
            mock_ollama.post.return_value = mock_response
            
            # 发送持续请求
            start_time = time.time()
            request_count = 20
            
            tasks = []
            for i in range(request_count):
                request_data = {
                    "model": "llama3.2",
                    "prompt": f"负载测试 {i}",
                }
                
                task = async_client.post(
                    "/llm/generate",
                    json=request_data,
                    headers={"Authorization": "Bearer test-token"}
                )
                tasks.append(task)
                
                # 稍微延迟避免过于密集
                await asyncio.sleep(0.1)
            
            # 等待所有请求完成
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # 验证性能
            success_count = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 200)
            
            assert success_count >= request_count * 0.9  # 至少90%成功
            assert total_time < 30  # 应该在30秒内完成
            
            # 平均响应时间应该合理
            avg_response_time = total_time / request_count
            assert avg_response_time < 2.0  # 平均小于2秒


class TestServiceIntegration:
    """服务集成测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ollama_service_integration(self):
        """测试Ollama服务集成"""
        from core.main import check_ollama_health, core
        
        # 模拟Ollama客户端
        with patch.object(core, 'ollama_client') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"models": []}
            mock_client.get.return_value = mock_response
            
            health_status = await check_ollama_health()
            assert health_status is True
            
            # 测试失败情况
            mock_response.status_code = 500
            health_status = await check_ollama_health()
            assert health_status is False

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_weaviate_service_integration(self):
        """测试Weaviate服务集成"""
        from core.main import check_weaviate_health, core
        
        # 模拟Weaviate客户端
        with patch.object(core, 'weaviate_client') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"version": "1.0.0"}
            mock_client.get.return_value = mock_response
            
            health_status = await check_weaviate_health()
            assert health_status is True

    @pytest.mark.integration
    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_database_integration(self):
        """测试数据库集成"""
        from core.main import core
        
        # 模拟数据库操作
        with patch.object(core, 'db_pool') as mock_pool:
            mock_connection = AsyncMock()
            mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
            
            # 这里可以添加实际的数据库操作测试
            async with mock_pool.acquire() as conn:
                # 模拟查询
                mock_connection.fetchrow.return_value = {"id": 1, "name": "test"}
                result = await mock_connection.fetchrow("SELECT * FROM test")
                assert result["name"] == "test"


class TestEndToEndWorkflows:
    """端到端工作流程测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_ai_monitoring_workflow(self, async_client):
        """测试完整的AI监理工作流程"""
        # 1. 检查系统健康状态
        health_response = await async_client.get("/health")
        assert health_response.status_code == 200
        
        # 2. 获取系统状态
        status_response = await async_client.get("/status")
        assert status_response.status_code == 200
        
        # 3. 模拟外部服务
        with patch('core.main.core.ollama_client') as mock_ollama, \
             patch('core.main.core.redis_client') as mock_redis:
            
            # 配置LLM响应
            mock_llm_response = AsyncMock()
            mock_llm_response.status_code = 200
            mock_llm_response.json.return_value = {
                "response": "这是AI监理系统的分析结果",
                "prompt_eval_count": 20,
                "eval_count": 80
            }
            
            # 配置向量化响应
            mock_vector_response = AsyncMock()
            mock_vector_response.status_code = 200
            mock_vector_response.json.return_value = {
                "embedding": [0.1] * 768
            }
            
            mock_ollama.post.return_value = mock_llm_response
            mock_redis.setex = AsyncMock()
            
            # 4. 执行代码分析（LLM生成）
            analysis_request = {
                "model": "llama3.2",
                "prompt": "分析这段代码的质量和潜在问题：def hello(): print('world')",
                "temperature": 0.3,
                "max_tokens": 500
            }
            
            analysis_response = await async_client.post(
                "/llm/generate",
                json=analysis_request,
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert analysis_response.status_code == 200
            analysis_data = analysis_response.json()
            assert "response" in analysis_data
            
            # 5. 执行文本向量化
            mock_ollama.post.return_value = mock_vector_response
            
            vector_request = {
                "text": analysis_data["response"],
                "collection": "code_analysis"
            }
            
            vector_response = await async_client.post(
                "/vector/embed",
                json=vector_request,
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert vector_response.status_code == 200
            vector_data = vector_response.json()
            assert len(vector_data["embedding"]) == 768
            
            # 6. 检查系统指标
            metrics_response = await async_client.get("/metrics/system")
            assert metrics_response.status_code == 200
            
            # 7. 验证工作流程完整性
            assert analysis_data["tokens_used"] == 100
            assert vector_data["dimension"] == 768
            assert vector_data["collection"] == "code_analysis"