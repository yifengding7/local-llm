"""
性能测试
"""
import pytest
import asyncio
import time
import statistics
from unittest.mock import patch, AsyncMock
import httpx


class TestAPIPerformance:
    """API性能测试"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_health_check_latency(self, async_client):
        """测试健康检查延迟"""
        latencies = []
        iterations = 20
        
        for _ in range(iterations):
            start_time = time.time()
            response = await async_client.get("/health")
            end_time = time.time()
            
            assert response.status_code == 200
            latency = (end_time - start_time) * 1000  # 转换为毫秒
            latencies.append(latency)
            
            await asyncio.sleep(0.1)  # 短暂间隔
        
        # 计算统计数据
        avg_latency = statistics.mean(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
        p99_latency = statistics.quantiles(latencies, n=100)[98]  # 99th percentile
        
        # 性能断言
        assert avg_latency < 100, f"平均延迟过高: {avg_latency:.2f}ms"
        assert p95_latency < 200, f"P95延迟过高: {p95_latency:.2f}ms"
        assert p99_latency < 500, f"P99延迟过高: {p99_latency:.2f}ms"
        
        print(f"健康检查性能统计:")
        print(f"  平均延迟: {avg_latency:.2f}ms")
        print(f"  P95延迟: {p95_latency:.2f}ms")
        print(f"  P99延迟: {p99_latency:.2f}ms")

    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_llm_generation_throughput(self, async_client):
        """测试LLM生成吞吐量"""
        # 模拟Ollama响应
        with patch('core.main.core.ollama_client') as mock_ollama:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "response": "性能测试响应内容" * 10,  # 模拟较长响应
                "prompt_eval_count": 15,
                "eval_count": 85
            }
            mock_ollama.post.return_value = mock_response
            
            # 配置测试参数
            concurrent_users = 10
            requests_per_user = 5
            total_requests = concurrent_users * requests_per_user
            
            async def user_requests(user_id):
                """模拟单个用户的请求"""
                user_latencies = []
                
                for i in range(requests_per_user):
                    request_data = {
                        "model": "llama3.2",
                        "prompt": f"用户{user_id}的第{i+1}个请求：请分析这段代码",
                        "temperature": 0.7,
                        "max_tokens": 200
                    }
                    
                    start_time = time.time()
                    response = await async_client.post(
                        "/llm/generate",
                        json=request_data,
                        headers={"Authorization": "Bearer test-token"}
                    )
                    end_time = time.time()
                    
                    assert response.status_code == 200
                    latency = (end_time - start_time) * 1000
                    user_latencies.append(latency)
                    
                    # 短暂间隔模拟真实使用
                    await asyncio.sleep(0.2)
                
                return user_latencies
            
            # 执行并发测试
            start_time = time.time()
            tasks = [user_requests(i) for i in range(concurrent_users)]
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            # 收集所有延迟数据
            all_latencies = []
            for user_latencies in results:
                all_latencies.extend(user_latencies)
            
            total_time = end_time - start_time
            throughput = total_requests / total_time  # 请求/秒
            avg_latency = statistics.mean(all_latencies)
            
            # 性能断言
            assert throughput > 5, f"吞吐量过低: {throughput:.2f} req/s"
            assert avg_latency < 1000, f"平均延迟过高: {avg_latency:.2f}ms"
            
            print(f"LLM生成性能统计:")
            print(f"  总请求数: {total_requests}")
            print(f"  总耗时: {total_time:.2f}s")
            print(f"  吞吐量: {throughput:.2f} req/s")
            print(f"  平均延迟: {avg_latency:.2f}ms")

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_vector_embedding_performance(self, async_client):
        """测试向量化性能"""
        # 模拟Ollama向量化响应
        with patch('core.main.core.ollama_client') as mock_ollama, \
             patch('core.main.core.redis_client') as mock_redis:
            
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "embedding": [0.1] * 768
            }
            mock_ollama.post.return_value = mock_response
            mock_redis.setex = AsyncMock()
            
            # 测试不同长度的文本
            test_texts = [
                "短文本",
                "中等长度的测试文本，包含更多内容来测试性能表现",
                "这是一个很长的测试文本，用于测试向量化功能在处理大量文本时的性能表现。" * 10
            ]
            
            performance_results = {}
            
            for text_type, text in zip(["短", "中", "长"], test_texts):
                latencies = []
                iterations = 10
                
                for _ in range(iterations):
                    request_data = {
                        "text": text,
                        "collection": "performance_test"
                    }
                    
                    start_time = time.time()
                    response = await async_client.post(
                        "/vector/embed",
                        json=request_data,
                        headers={"Authorization": "Bearer test-token"}
                    )
                    end_time = time.time()
                    
                    assert response.status_code == 200
                    latency = (end_time - start_time) * 1000
                    latencies.append(latency)
                    
                    await asyncio.sleep(0.1)
                
                avg_latency = statistics.mean(latencies)
                performance_results[text_type] = avg_latency
                
                # 性能断言
                assert avg_latency < 500, f"{text_type}文本向量化延迟过高: {avg_latency:.2f}ms"
            
            print(f"向量化性能统计:")
            for text_type, avg_latency in performance_results.items():
                print(f"  {text_type}文本平均延迟: {avg_latency:.2f}ms")

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_mixed_requests(self, async_client):
        """测试混合并发请求性能"""
        # 模拟所有外部服务
        with patch('core.main.core.ollama_client') as mock_ollama, \
             patch('core.main.core.redis_client') as mock_redis:
            
            # 配置LLM响应
            mock_llm_response = AsyncMock()
            mock_llm_response.status_code = 200
            mock_llm_response.json.return_value = {
                "response": "混合测试响应",
                "prompt_eval_count": 10,
                "eval_count": 40
            }
            
            # 配置向量化响应
            mock_vector_response = AsyncMock()
            mock_vector_response.status_code = 200
            mock_vector_response.json.return_value = {
                "embedding": [0.1] * 768
            }
            
            # 根据请求路径返回不同响应
            def mock_post_side_effect(url, **kwargs):
                if "/api/generate" in str(url):
                    return mock_llm_response
                elif "/api/embeddings" in str(url):
                    return mock_vector_response
                return mock_llm_response
            
            mock_ollama.post.side_effect = mock_post_side_effect
            mock_redis.setex = AsyncMock()
            
            async def mixed_requests():
                """执行混合类型的请求"""
                tasks = []
                
                # LLM生成请求
                for i in range(5):
                    llm_request = async_client.post(
                        "/llm/generate",
                        json={
                            "model": "llama3.2",
                            "prompt": f"混合测试LLM请求 {i}",
                            "max_tokens": 100
                        },
                        headers={"Authorization": "Bearer test-token"}
                    )
                    tasks.append(llm_request)
                
                # 向量化请求
                for i in range(5):
                    vector_request = async_client.post(
                        "/vector/embed",
                        json={
                            "text": f"混合测试向量化文本 {i}",
                            "collection": "mixed_test"
                        },
                        headers={"Authorization": "Bearer test-token"}
                    )
                    tasks.append(vector_request)
                
                # 健康检查请求
                for i in range(10):
                    health_request = async_client.get("/health")
                    tasks.append(health_request)
                
                return await asyncio.gather(*tasks)
            
            # 执行测试
            start_time = time.time()
            responses = await mixed_requests()
            end_time = time.time()
            
            total_time = end_time - start_time
            total_requests = len(responses)
            throughput = total_requests / total_time
            
            # 验证所有请求成功
            success_count = sum(1 for r in responses if r.status_code in [200, 201])
            success_rate = success_count / total_requests * 100
            
            # 性能断言
            assert success_rate >= 95, f"成功率过低: {success_rate:.1f}%"
            assert throughput > 10, f"混合请求吞吐量过低: {throughput:.2f} req/s"
            assert total_time < 10, f"总响应时间过长: {total_time:.2f}s"
            
            print(f"混合并发请求性能统计:")
            print(f"  总请求数: {total_requests}")
            print(f"  成功率: {success_rate:.1f}%")
            print(f"  总耗时: {total_time:.2f}s")
            print(f"  吞吐量: {throughput:.2f} req/s")


class TestSystemPerformance:
    """系统性能测试"""

    @pytest.mark.performance
    def test_memory_usage(self):
        """测试内存使用情况"""
        import psutil
        import gc
        
        # 强制垃圾回收
        gc.collect()
        
        # 获取当前进程内存使用
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        # 内存使用断言
        assert memory_percent < 50, f"内存使用率过高: {memory_percent:.1f}%"
        assert memory_info.rss < 1024 * 1024 * 1024, f"RSS内存过大: {memory_info.rss / 1024 / 1024:.1f}MB"
        
        print(f"内存使用统计:")
        print(f"  RSS: {memory_info.rss / 1024 / 1024:.1f}MB")
        print(f"  VMS: {memory_info.vms / 1024 / 1024:.1f}MB")
        print(f"  内存使用率: {memory_percent:.1f}%")

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_startup_time(self):
        """测试应用启动时间"""
        from core.main import AIMonitorCore
        
        # 测试核心引擎初始化时间
        start_time = time.time()
        
        core = AIMonitorCore()
        
        # 模拟初始化
        with patch('aioredis.from_url'), \
             patch('asyncpg.create_pool'), \
             patch('httpx.AsyncClient'):
            
            await core.initialize()
            
        end_time = time.time()
        initialization_time = end_time - start_time
        
        # 启动时间断言
        assert initialization_time < 5.0, f"初始化时间过长: {initialization_time:.2f}s"
        
        print(f"启动性能统计:")
        print(f"  初始化时间: {initialization_time:.3f}s")

    @pytest.mark.performance
    @pytest.mark.slow
    def test_cpu_usage_under_load(self):
        """测试负载下的CPU使用情况"""
        import psutil
        import threading
        import time
        
        def cpu_intensive_task():
            """CPU密集型任务"""
            end_time = time.time() + 2  # 运行2秒
            while time.time() < end_time:
                # 模拟CPU密集型计算
                sum(i * i for i in range(1000))
        
        # 启动多个CPU密集型线程
        threads = []
        for _ in range(4):
            thread = threading.Thread(target=cpu_intensive_task)
            threads.append(thread)
        
        # 监控CPU使用率
        cpu_usages = []
        
        # 启动线程
        for thread in threads:
            thread.start()
        
        # 监控期间收集CPU使用率
        for _ in range(10):
            cpu_percent = psutil.cpu_percent(interval=0.2)
            cpu_usages.append(cpu_percent)
        
        # 等待线程完成
        for thread in threads:
            thread.join()
        
        max_cpu = max(cpu_usages)
        avg_cpu = sum(cpu_usages) / len(cpu_usages)
        
        # CPU使用率应该在合理范围内
        assert max_cpu < 90, f"最大CPU使用率过高: {max_cpu:.1f}%"
        
        print(f"负载下CPU使用统计:")
        print(f"  平均CPU使用率: {avg_cpu:.1f}%")
        print(f"  最大CPU使用率: {max_cpu:.1f}%")


class TestDatabasePerformance:
    """数据库性能测试"""

    @pytest.mark.performance
    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_connection_pool_performance(self):
        """测试数据库连接池性能"""
        from core.main import core
        
        # 模拟数据库连接池
        with patch.object(core, 'db_pool') as mock_pool:
            mock_connection = AsyncMock()
            mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
            mock_connection.fetchrow.return_value = {"id": 1, "data": "test"}
            
            # 测试并发数据库查询
            async def db_query(query_id):
                async with mock_pool.acquire() as conn:
                    start_time = time.time()
                    result = await conn.fetchrow(f"SELECT * FROM test WHERE id = {query_id}")
                    end_time = time.time()
                    return end_time - start_time
            
            # 并发执行多个查询
            start_time = time.time()
            tasks = [db_query(i) for i in range(20)]
            query_times = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
            
            avg_query_time = sum(query_times) / len(query_times) * 1000  # 转换为毫秒
            throughput = len(tasks) / total_time
            
            # 性能断言
            assert avg_query_time < 100, f"数据库查询延迟过高: {avg_query_time:.2f}ms"
            assert throughput > 50, f"数据库查询吞吐量过低: {throughput:.2f} queries/s"
            
            print(f"数据库性能统计:")
            print(f"  平均查询时间: {avg_query_time:.2f}ms")
            print(f"  查询吞吐量: {throughput:.2f} queries/s")