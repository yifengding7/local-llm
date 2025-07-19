#!/usr/bin/env python3
"""
AI监理系统 v2.1 - 快速状态检查
"""

import httpx
import asyncio
import psutil
import subprocess
from datetime import datetime

class StatusChecker:
    def __init__(self):
        self.services = {
            "Python核心服务": "http://localhost:8000/health",
            "Ollama LLM引擎": "http://localhost:11434/api/tags", 
            "Weaviate向量库": "http://localhost:8080/v1/meta",
            "Go闪电API": "http://localhost:3001/health",
            "Rust零延迟引擎": "http://localhost:3002/health"
        }
    
    async def check_service(self, name, url):
        """检查单个服务"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=3.0)
                if response.status_code == 200:
                    # 尝试获取更多信息
                    try:
                        data = response.json()
                        if name == "Python核心服务":
                            uptime = data.get('uptime', 0)
                            return f"✅ {name}: 运行中 (运行时间: {uptime}秒)"
                        elif name == "Ollama LLM引擎":
                            models = data.get('models', [])
                            return f"✅ {name}: 运行中 ({len(models)}个模型)"
                        else:
                            return f"✅ {name}: 运行中"
                    except:
                        return f"✅ {name}: 运行中"
                else:
                    return f"⚠️  {name}: 响应异常 (HTTP {response.status_code})"
        except httpx.ConnectError:
            return f"❌ {name}: 未运行 (连接失败)"
        except httpx.TimeoutException:
            return f"⚠️  {name}: 响应超时"
        except Exception as e:
            return f"❌ {name}: 错误 ({type(e).__name__})"
    
    def check_port(self, port):
        """检查端口是否被占用"""
        try:
            result = subprocess.run(
                ['lsof', '-i', f':{port}'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def get_system_info(self):
        """获取系统信息"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "CPU使用率": f"{cpu_percent}%",
            "内存使用": f"{memory.percent}% ({memory.used / 1e9:.1f}GB / {memory.total / 1e9:.1f}GB)",
            "磁盘使用": f"{disk.percent}% ({disk.used / 1e9:.1f}GB / {disk.total / 1e9:.1f}GB)"
        }
    
    async def run(self):
        """运行状态检查"""
        print("🔍 AI监理系统 v2.1 - 状态检查")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        # 检查服务状态
        print("\n📊 服务状态:")
        tasks = []
        for name, url in self.services.items():
            tasks.append(self.check_service(name, url))
        
        results = await asyncio.gather(*tasks)
        for result in results:
            print(f"  {result}")
        
        # 检查端口
        print("\n🔌 端口状态:")
        ports = {
            8000: "核心API",
            11434: "Ollama",
            8080: "Weaviate",
            3001: "Go API",
            3002: "Rust引擎",
            6379: "Redis",
            9090: "Prometheus"
        }
        
        for port, service in ports.items():
            if self.check_port(port):
                print(f"  ✅ 端口 {port} ({service}): 已占用")
            else:
                print(f"  ⭕ 端口 {port} ({service}): 空闲")
        
        # 系统资源
        print("\n💻 系统资源:")
        system_info = self.get_system_info()
        for key, value in system_info.items():
            print(f"  {key}: {value}")
        
        # 快速链接
        print("\n🔗 快速访问:")
        print("  核心API文档: http://localhost:8000/docs")
        print("  健康检查: http://localhost:8000/health")
        print("  系统状态: http://localhost:8000/status")
        print("  Ollama模型: http://localhost:11434/api/tags")
        
        print("\n✅ 检查完成")

async def main():
    checker = StatusChecker()
    await checker.run()

if __name__ == "__main__":
    asyncio.run(main())
