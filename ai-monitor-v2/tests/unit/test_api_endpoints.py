"""
API端点单元测试
"""
import pytest
import time
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import httpx

from core.main import app


class TestHealthEndpoint:
    """健康检查端点测试"""

    @pytest.mark.unit
    def test_health_check_success(self, client):
        """测试健康检查成功"""
        with patch('core.main.check_ollama_health', return_value=True), \
             patch('core.main.check_weaviate_health', return_value=True), \
             patch('core.main.core.get_system_metrics') as mock_metrics:
            
            # 配置系统指标mock
            mock_metrics.return_value = MagicMock(
                cpu_percent=25.0,
                memory_percent=45.0
            )
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "healthy"
            assert "timestamp" in data
            assert "version" in data
            assert "uptime" in data
            assert "system" in data
            assert data["system"]["cpu_percent"] == 25.0
            assert data["system"]["memory_percent"] == 45.0

    @pytest.mark.unit
    def test_health_check_with_service_failures(self, client):
        """测试服务故障时的健康检查"""
        with patch('core.main.check_ollama_health', return_value=False), \
             patch('core.main.check_weaviate_health', return_value=False), \
             patch('core.main.core.get_system_metrics') as mock_metrics:
            
            mock_metrics.return_value = MagicMock(
                cpu_percent=85.0,
                memory_percent=90.0
            )
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["system"]["ollama_available"] is False
            assert data["system"]["weaviate_available"] is False


class TestLLMEndpoint:
    """LLM生成端点测试"""

    @pytest.mark.unit
    def test_llm_generate_success(self, client):
        """测试LLM生成成功"""
        with patch('core.main.core.process_llm_request') as mock_process:
            # 配置mock返回值
            mock_process.return_value = MagicMock(
                response="测试生成的文本",
                model="llama3.2",
                tokens_used=100,
                processing_time=1.5,
                timestamp=int(time.time())
            )
            
            request_data = {
                "model": "llama3.2",
                "prompt": "测试提示词",
                "temperature": 0.7,
                "max_tokens": 100
            }
            
            response = client.post(
                "/llm/generate",
                json=request_data,
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["response"] == "测试生成的文本"
            assert data["model"] == "llama3.2"
            assert data["tokens_used"] == 100
            assert data["processing_time"] == 1.5

    @pytest.mark.unit
    def test_llm_generate_validation_error(self, client):
        """测试LLM生成参数验证错误"""
        # 缺少必需字段
        request_data = {
            "prompt": "测试提示词"
            # 缺少model字段
        }
        
        response = client.post(
            "/llm/generate",
            json=request_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 422  # 验证错误

    @pytest.mark.unit
    def test_llm_generate_invalid_temperature(self, client):
        """测试LLM生成无效温度参数"""
        request_data = {
            "model": "llama3.2",
            "prompt": "测试提示词",
            "temperature": 3.0  # 超出有效范围
        }
        
        response = client.post(
            "/llm/generate",
            json=request_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 422

    @pytest.mark.unit
    def test_llm_generate_unauthorized(self, client):
        """测试未授权访问LLM生成"""
        request_data = {
            "model": "llama3.2",
            "prompt": "测试提示词"
        }
        
        response = client.post("/llm/generate", json=request_data)
        
        assert response.status_code == 403  # 未授权

    @pytest.mark.unit
    def test_llm_generate_processing_error(self, client):
        """测试LLM处理错误"""
        with patch('core.main.core.process_llm_request', side_effect=Exception("Ollama服务错误")):
            request_data = {
                "model": "llama3.2",
                "prompt": "测试提示词"
            }
            
            response = client.post(
                "/llm/generate",
                json=request_data,
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 500


class TestVectorEndpoint:
    """向量化端点测试"""

    @pytest.mark.unit
    def test_vector_embed_success(self, client):
        """测试向量化成功"""
        with patch('core.main.core.process_vector_request') as mock_process:
            # 配置mock返回值
            embedding_data = [0.1, 0.2, 0.3] * 256  # 768维向量
            mock_process.return_value = MagicMock(
                embedding=embedding_data,
                dimension=len(embedding_data),
                text="测试文本",
                collection="default",
                timestamp=int(time.time())
            )
            
            request_data = {
                "text": "测试文本",
                "collection": "default"
            }
            
            response = client.post(
                "/vector/embed",
                json=request_data,
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["text"] == "测试文本"
            assert data["collection"] == "default"
            assert data["dimension"] == len(embedding_data)
            assert len(data["embedding"]) == len(embedding_data)

    @pytest.mark.unit
    def test_vector_embed_empty_text(self, client):
        """测试空文本向量化"""
        request_data = {
            "text": "",  # 空文本
            "collection": "default"
        }
        
        response = client.post(
            "/vector/embed",
            json=request_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 422

    @pytest.mark.unit
    def test_vector_embed_unauthorized(self, client):
        """测试未授权向量化请求"""
        request_data = {
            "text": "测试文本"
        }
        
        response = client.post("/vector/embed", json=request_data)
        
        assert response.status_code == 403


class TestMetricsEndpoints:
    """指标端点测试"""

    @pytest.mark.unit
    def test_system_metrics(self, client):
        """测试系统指标端点"""
        with patch('core.main.core.get_system_metrics') as mock_metrics:
            mock_metrics.return_value = MagicMock(
                cpu_percent=25.0,
                memory_percent=45.0,
                memory_used=8 * 1024 * 1024 * 1024,
                memory_total=16 * 1024 * 1024 * 1024,
                disk_usage={
                    "total": 1000 * 1024 * 1024 * 1024,
                    "used": 500 * 1024 * 1024 * 1024,
                    "free": 500 * 1024 * 1024 * 1024,
                    "percent": 50.0
                },
                network_io={
                    "bytes_sent": 1024 * 1024,
                    "bytes_recv": 2 * 1024 * 1024
                },
                load_average=[1.0, 1.5, 2.0],
                timestamp=int(time.time())
            )
            
            response = client.get("/metrics/system")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["cpu_percent"] == 25.0
            assert data["memory_percent"] == 45.0
            assert "disk_usage" in data
            assert "network_io" in data
            assert "load_average" in data

    @pytest.mark.unit
    def test_prometheus_metrics(self, client):
        """测试Prometheus指标端点"""
        response = client.get("/metrics/prometheus")
        
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        
        # 检查指标内容
        content = response.text
        assert "ai_monitor_requests_total" in content
        assert "ai_monitor_request_duration_seconds" in content
        assert "ai_monitor_active_connections" in content

    @pytest.mark.unit
    def test_status_endpoint(self, client):
        """测试状态端点"""
        response = client.get("/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["service"] == "AI监理系统v2.1"
        assert data["version"] == "2.1.0"
        assert "uptime" in data
        assert "timestamp" in data
        assert "environment" in data
        assert "python_version" in data["environment"]


class TestMiddleware:
    """中间件测试"""

    @pytest.mark.unit
    def test_cors_middleware(self, client):
        """测试CORS中间件"""
        response = client.options("/health", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })
        
        # 检查CORS头部
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "*"

    @pytest.mark.unit
    def test_gzip_middleware(self, client):
        """测试GZip压缩中间件"""
        response = client.get("/health", headers={
            "Accept-Encoding": "gzip"
        })
        
        assert response.status_code == 200
        # 实际的压缩检查需要更复杂的设置

    @pytest.mark.unit
    def test_metrics_middleware(self, client):
        """测试指标中间件"""
        with patch('core.main.core') as mock_core:
            mock_core.active_connections = 0
            
            # 发送请求
            response = client.get("/health")
            
            assert response.status_code == 200
            # 指标中间件应该记录请求


class TestAuthentication:
    """认证测试"""

    @pytest.mark.unit
    def test_bearer_token_required(self, client):
        """测试Bearer token要求"""
        # 需要认证的端点
        protected_endpoints = [
            "/llm/generate",
            "/vector/embed"
        ]
        
        for endpoint in protected_endpoints:
            response = client.post(endpoint, json={})
            assert response.status_code == 403

    @pytest.mark.unit
    def test_valid_bearer_token(self, client):
        """测试有效Bearer token"""
        headers = {"Authorization": "Bearer valid-token"}
        
        # 这里只测试认证机制，不测试实际业务逻辑
        with patch('core.main.core.process_llm_request'):
            response = client.post(
                "/llm/generate",
                json={
                    "model": "test",
                    "prompt": "test"
                },
                headers=headers
            )
            
            # 应该通过认证（不是403）
            assert response.status_code != 403


class TestErrorHandling:
    """错误处理测试"""

    @pytest.mark.unit
    def test_404_handling(self, client):
        """测试404错误处理"""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404

    @pytest.mark.unit
    def test_method_not_allowed(self, client):
        """测试方法不允许错误"""
        response = client.put("/health")  # health只支持GET
        assert response.status_code == 405

    @pytest.mark.unit
    def test_request_validation_error(self, client):
        """测试请求验证错误"""
        # 发送无效JSON
        response = client.post(
            "/llm/generate",
            data="invalid json",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer test-token"
            }
        )
        
        assert response.status_code == 422