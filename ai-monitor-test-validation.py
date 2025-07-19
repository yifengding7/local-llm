#!/usr/bin/env python3
"""
AI监理系统 v2.1 - 自动化测试验收程序
完整验证系统功能和性能
"""

import os
import sys
import time
import json
import asyncio
import httpx
import psutil
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 测试结果枚举
class TestStatus(Enum):
    PASS = "✅ 通过"
    FAIL = "❌ 失败"
    WARN = "⚠️ 警告"
    SKIP = "⏭️ 跳过"

@dataclass
class TestResult:
    """测试结果"""
    name: str
    status: TestStatus
    message: str
    duration: float
    details: Dict[str, Any] = None

class SystemValidator:
    """系统验收器"""
    
    def __init__(self):
        self.api_base = "http://localhost:8000"
        self.api_key = os.getenv("API_KEY", "test-key")
        self.results: List[TestResult] = []
        self.start_time = time.time()
        
    async def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*60)
        print("🧪 AI监理系统 v2.1 - 自动化测试验收")
        print("="*60 + "\n")
        
        # 1. 环境检查
        await self.test_environment()
        
        # 2. 服务健康检查
        await self.test_services_health()
        
        # 3. API功能测试
        await self.test_api_functionality()
        
        # 4. 性能测试
        await self.test_performance()
        
        # 5. 资源使用测试
        await self.test_resource_usage()
        
        # 6. 隔离性测试
        await self.test_isolation()
        
        # 生成报告
        self.generate_report()
    
    async def test_environment(self):
        """测试环境检查"""
        print("\n📋 环境检查")
        print("-" * 40)
        
        tests = [
            self._check_python_version(),
            self._check_docker(),
            self._check_ollama(),
            self._check_disk_space(),
            self._check_memory()
        ]
        
        for test in tests:
            self.results.append(await test)
            self._print_result(self.results[-1])
    
    async def _check_python_version(self) -> TestResult:
        """检查Python版本"""
        start = time.time()
        try:
            version = sys.version_info
            if version.major == 3 and version.minor >= 9:
                return TestResult(
                    "Python版本",
                    TestStatus.PASS,
                    f"Python {version.major}.{version.minor}.{version.micro}",
                    time.time() - start
                )
            else:
                return TestResult(
                    "Python版本",
                    TestStatus.FAIL,
                    f"需要Python 3.9+，当前: {version.major}.{version.minor}",
                    time.time() - start
                )
        except Exception as e:
            return TestResult(
                "Python版本",
                TestStatus.FAIL,
                str(e),
                time.time() - start
            )
    
    async def _check_docker(self) -> TestResult:
        """检查Docker"""
        start = time.time()
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return TestResult(
                    "Docker服务",
                    TestStatus.PASS,
                    "Docker正在运行",
                    time.time() - start
                )
            else:
                return TestResult(
                    "Docker服务",
                    TestStatus.FAIL,
                    "Docker未运行",
                    time.time() - start
                )
        except FileNotFoundError:
            return TestResult(
                "Docker服务",
                TestStatus.FAIL,
                "Docker未安装",
                time.time() - start
            )
    
    async def _check_ollama(self) -> TestResult:
        """检查Ollama"""
        start = time.time()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:11434/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    return TestResult(
                        "Ollama服务",
                        TestStatus.PASS,
                        f"运行中，已加载{len(models)}个模型",
                        time.time() - start,
                        {"models": [m["name"] for m in models]}
                    )
        except:
            return TestResult(
                "Ollama服务",
                TestStatus.FAIL,
                "Ollama未运行或无法连接",
                time.time() - start
            )
    
    async def _check_disk_space(self) -> TestResult:
        """检查磁盘空间"""
        start = time.time()
        disk = psutil.disk_usage('/')
        free_gb = disk.free / (1024**3)
        
        if free_gb > 20:
            status = TestStatus.PASS
            message = f"可用空间: {free_gb:.1f}GB"
        elif free_gb > 10:
            status = TestStatus.WARN
            message = f"可用空间较少: {free_gb:.1f}GB"
        else:
            status = TestStatus.FAIL
            message = f"磁盘空间不足: {free_gb:.1f}GB"
        
        return TestResult(
            "磁盘空间",
            status,
            message,
            time.time() - start,
            {"free_gb": free_gb, "percent_used": disk.percent}
        )
    
    async def _check_memory(self) -> TestResult:
        """检查内存"""
        start = time.time()
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        
        if available_gb > 8:
            status = TestStatus.PASS
            message = f"可用内存: {available_gb:.1f}GB"
        elif available_gb > 4:
            status = TestStatus.WARN
            message = f"可用内存较少: {available_gb:.1f}GB"
        else:
            status = TestStatus.FAIL
            message = f"内存不足: {available_gb:.1f}GB"
        
        return TestResult(
            "系统内存",
            status,
            message,
            time.time() - start,
            {"available_gb": available_gb, "percent_used": memory.percent}
        )
    
    async def test_services_health(self):
        """测试服务健康状态"""
        print("\n🏥 服务健康检查")
        print("-" * 40)
        
        services = [
            ("API服务", f"{self.api_base}/health"),
            ("Weaviate", "http://localhost:8080/v1/.well-known/ready"),
            ("Redis", None),  # 特殊处理
            ("Prometheus", "http://localhost:9090/-/healthy")
        ]
        
        for name, url in services:
            if name == "Redis":
                result = await self._check_redis()
            else:
                result = await self._check_service(name, url)
            
            self.results.append(result)
            self._print_result(result)
    
    async def _check_service(self, name: str, url: str) -> TestResult:
        """检查单个服务"""
        start = time.time()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=5.0)
                if response.status_code == 200:
                    return TestResult(
                        name,
                        TestStatus.PASS,
                        "服务正常",
                        time.time() - start
                    )
                else:
                    return TestResult(
                        name,
                        TestStatus.FAIL,
                        f"状态码: {response.status_code}",
                        time.time() - start
                    )
        except Exception as e:
            return TestResult(
                name,
                TestStatus.FAIL,
                f"连接失败: {str(e)}",
                time.time() - start
            )
    
    async def _check_redis(self) -> TestResult:
        """检查Redis"""
        start = time.time()
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379)
            r.ping()
            return TestResult(
                "Redis",
                TestStatus.PASS,
                "服务正常",
                time.time() - start
            )
        except:
            return TestResult(
                "Redis",
                TestStatus.FAIL,
                "无法连接到Redis",
                time.time() - start
            )
    
    async def test_api_functionality(self):
        """测试API功能"""
        print("\n🔌 API功能测试")
        print("-" * 40)
        
        # 测试各个API端点
        tests = [
            self._test_chat_api(),
            self._test_code_monitor_api(),
            self._test_embedding_api(),
            self._test_vector_search_api()
        ]
        
        for test in tests:
            result = await test
            self.results.append(result)
            self._print_result(result)
    
    async def _test_chat_api(self) -> TestResult:
        """测试聊天API"""
        start = time.time()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": "phi3:mini",
                        "messages": [{"role": "user", "content": "Hello"}],
                        "max_tokens": 10
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return TestResult(
                        "聊天API",
                        TestStatus.PASS,
                        "响应正常",
                        time.time() - start,
                        {"response": data.get("choices", [{}])[0].get("message", {}).get("content", "")}
                    )
                else:
                    return TestResult(
                        "聊天API",
                        TestStatus.FAIL,
                        f"状态码: {response.status_code}",
                        time.time() - start
                    )
        except Exception as e:
            return TestResult(
                "聊天API",
                TestStatus.FAIL,
                str(e),
                time.time() - start
            )
    
    async def _test_code_monitor_api(self) -> TestResult:
        """测试代码监理API"""
        start = time.time()
        try:
            test_code = '''def hello():
    print("Hello World")
    x = [1,2,3]
    for i in range(len(x)):
        print(x[i])
'''
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/v1/monitor/analyze",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "file_path": "test.py",
                        "content": test_code
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    issues = data.get("issues", [])
                    return TestResult(
                        "代码监理API",
                        TestStatus.PASS,
                        f"发现{len(issues)}个问题",
                        time.time() - start,
                        {"issues_count": len(issues)}
                    )
                else:
                    return TestResult(
                        "代码监理API",
                        TestStatus.FAIL,
                        f"状态码: {response.status_code}",
                        time.time() - start
                    )
        except Exception as e:
            return TestResult(
                "代码监理API",
                TestStatus.FAIL,
                str(e),
                time.time() - start
            )
    
    async def _test_embedding_api(self) -> TestResult:
        """测试嵌入API"""
        start = time.time()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/v1/embeddings",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "input": "Test embedding",
                        "model": "nomic-embed-text"
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    embedding = data.get("data", [{}])[0].get("embedding", [])
                    return TestResult(
                        "嵌入API",
                        TestStatus.PASS,
                        f"生成{len(embedding)}维向量",
                        time.time() - start,
                        {"dimension": len(embedding)}
                    )
                else:
                    return TestResult(
                        "嵌入API",
                        TestStatus.FAIL,
                        f"状态码: {response.status_code}",
                        time.time() - start
                    )
        except Exception as e:
            return TestResult(
                "嵌入API",
                TestStatus.FAIL,
                str(e),
                time.time() - start
            )
    
    async def _test_vector_search_api(self) -> TestResult:
        """测试向量搜索API"""
        start = time.time()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/v1/vector/search",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "query": "AI监理系统",
                        "limit": 5
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    query_time = data.get("query_time_ms", 0)
                    
                    if query_time < 50:
                        status = TestStatus.PASS
                        message = f"查询延迟: {query_time:.1f}ms"
                    else:
                        status = TestStatus.WARN
                        message = f"查询延迟较高: {query_time:.1f}ms"
                    
                    return TestResult(
                        "向量搜索API",
                        status,
                        message,
                        time.time() - start,
                        {"query_time_ms": query_time}
                    )
                else:
                    return TestResult(
                        "向量搜索API",
                        TestStatus.FAIL,
                        f"状态码: {response.status_code}",
                        time.time() - start
                    )
        except Exception as e:
            return TestResult(
                "向量搜索API",
                TestStatus.FAIL,
                str(e),
                time.time() - start
            )
    
    async def test_performance(self):
        """性能测试"""
        print("\n⚡ 性能测试")
        print("-" * 40)
        
        # 并发测试
        result = await self._test_concurrent_requests()
        self.results.append(result)
        self._print_result(result)
        
        # 延迟测试
        result = await self._test_latency()
        self.results.append(result)
        self._print_result(result)
    
    async def _test_concurrent_requests(self) -> TestResult:
        """并发请求测试"""
        start = time.time()
        concurrent = 10
        
        async def make_request():
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/health",
                    timeout=10.0
                )
                return response.status_code == 200
        
        try:
            tasks = [make_request() for _ in range(concurrent)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            success = sum(1 for r in results if r is True)
            
            if success == concurrent:
                return TestResult(
                    "并发请求测试",
                    TestStatus.PASS,
                    f"{concurrent}个并发请求全部成功",
                    time.time() - start
                )
            else:
                return TestResult(
                    "并发请求测试",
                    TestStatus.WARN,
                    f"{success}/{concurrent}个请求成功",
                    time.time() - start
                )
        except Exception as e:
            return TestResult(
                "并发请求测试",
                TestStatus.FAIL,
                str(e),
                time.time() - start
            )
    
    async def _test_latency(self) -> TestResult:
        """延迟测试"""
        start = time.time()
        latencies = []
        
        try:
            async with httpx.AsyncClient() as client:
                for _ in range(10):
                    req_start = time.time()
                    response = await client.get(f"{self.api_base}/health")
                    latency = (time.time() - req_start) * 1000
                    latencies.append(latency)
            
            avg_latency = sum(latencies) / len(latencies)
            p99_latency = sorted(latencies)[int(len(latencies) * 0.99)]
            
            if avg_latency < 50:
                status = TestStatus.PASS
                message = f"平均延迟: {avg_latency:.1f}ms, P99: {p99_latency:.1f}ms"
            else:
                status = TestStatus.WARN
                message = f"延迟较高 - 平均: {avg_latency:.1f}ms, P99: {p99_latency:.1f}ms"
            
            return TestResult(
                "API延迟测试",
                status,
                message,
                time.time() - start,
                {"avg_ms": avg_latency, "p99_ms": p99_latency}
            )
        except Exception as e:
            return TestResult(
                "API延迟测试",
                TestStatus.FAIL,
                str(e),
                time.time() - start
            )
    
    async def test_resource_usage(self):
        """资源使用测试"""
        print("\n💻 资源使用测试")
        print("-" * 40)
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent < 50:
            status = TestStatus.PASS
            message = f"CPU使用率: {cpu_percent}%"
        elif cpu_percent < 80:
            status = TestStatus.WARN
            message = f"CPU使用率较高: {cpu_percent}%"
        else:
            status = TestStatus.FAIL
            message = f"CPU使用率过高: {cpu_percent}%"
        
        self.results.append(TestResult(
            "CPU使用率",
            status,
            message,
            0.0,
            {"percent": cpu_percent}
        ))
        self._print_result(self.results[-1])
        
        # 内存使用
        memory = psutil.virtual_memory()
        if memory.percent < 70:
            status = TestStatus.PASS
            message = f"内存使用率: {memory.percent}%"
        elif memory.percent < 85:
            status = TestStatus.WARN
            message = f"内存使用率较高: {memory.percent}%"
        else:
            status = TestStatus.FAIL
            message = f"内存使用率过高: {memory.percent}%"
        
        self.results.append(TestResult(
            "内存使用率",
            status,
            message,
            0.0,
            {"percent": memory.percent}
        ))
        self._print_result(self.results[-1])
    
    async def test_isolation(self):
        """隔离性测试"""
        print("\n🔒 环境隔离测试")
        print("-" * 40)
        
        # 检查虚拟环境
        venv_active = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
        )
        
        if venv_active:
            result = TestResult(
                "Python虚拟环境",
                TestStatus.PASS,
                "已激活虚拟环境",
                0.0
            )
        else:
            result = TestResult(
                "Python虚拟环境",
                TestStatus.WARN,
                "未使用虚拟环境",
                0.0
            )
        
        self.results.append(result)
        self._print_result(result)
        
        # 检查Docker容器
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "table {{.Names}}"],
                capture_output=True,
                text=True
            )
            
            containers = result.stdout.strip().split('\n')[1:]  # 跳过标题
            ai_containers = [c for c in containers if 'ai-monitor' in c]
            
            if len(ai_containers) >= 2:
                result = TestResult(
                    "Docker容器隔离",
                    TestStatus.PASS,
                    f"运行{len(ai_containers)}个隔离容器",
                    0.0,
                    {"containers": ai_containers}
                )
            else:
                result = TestResult(
                    "Docker容器隔离",
                    TestStatus.WARN,
                    "容器数量不足",
                    0.0
                )
        except:
            result = TestResult(
                "Docker容器隔离",
                TestStatus.FAIL,
                "无法检查Docker容器",
                0.0
            )
        
        self.results.append(result)
        self._print_result(result)
    
    def _print_result(self, result: TestResult):
        """打印测试结果"""
        print(f"{result.status.value} {result.name}: {result.message}")
        if result.details:
            for key, value in result.details.items():
                print(f"   └─ {key}: {value}")
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("📊 测试报告")
        print("="*60)
        
        # 统计结果
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == TestStatus.PASS)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAIL)
        warned = sum(1 for r in self.results if r.status == TestStatus.WARN)
        
        # 总耗时
        total_time = time.time() - self.start_time
        
        print(f"\n总测试数: {total}")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"⚠️ 警告: {warned}")
        print(f"\n总耗时: {total_time:.2f}秒")
        
        # 成功率
        success_rate = (passed / total) * 100 if total > 0 else 0
        print(f"成功率: {success_rate:.1f}%")
        
        # 验收结论
        print("\n" + "-"*40)
        if failed == 0 and warned <= 2:
            print("✅ 系统验收通过！")
            print("系统运行正常，可以投入使用。")
        elif failed == 0:
            print("⚠️ 系统基本通过验收")
            print("存在一些警告，建议优化后使用。")
        else:
            print("❌ 系统验收未通过")
            print("请修复失败的测试项后重试。")
        
        # 保存报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "warned": warned,
            "success_rate": success_rate,
            "total_time": total_time,
            "results": [
                {
                    "name": r.name,
                    "status": r.status.name,
                    "message": r.message,
                    "duration": r.duration,
                    "details": r.details
                }
                for r in self.results
            ]
        }
        
        with open("test_report.json", "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n详细报告已保存到: test_report.json")

async def main():
    """主函数"""
    validator = SystemValidator()
    await validator.run_all_tests()

if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())
