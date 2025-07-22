#!/usr/bin/env python3
"""
本地LLM项目健康检查工具
快速诊断系统状态和问题
"""

import subprocess
import json
import httpx
import asyncio
import psutil
from pathlib import Path
from datetime import datetime

class HealthChecker:
    def __init__(self):
        self.project_home = Path("/Users/imac/Documents/编程/项目/本地llm项目")
        self.services = {
            "Python核心服务": {
                "url": "http://localhost:8000/health",
                "port": 8000,
                "critical": True
            },
            "Ollama": {
                "url": "http://localhost:11434/api/tags",
                "port": 11434,
                "critical": True
            },
            "Weaviate": {
                "url": "http://localhost:8080/v1/meta",
                "port": 8080,
                "critical": False
            },
            "Go API": {
                "url": "http://localhost:3001/health",
                "port": 3001,
                "critical": False
            },
            "Rust引擎": {
                "url": "http://localhost:3002/health",
                "port": 3002,
                "critical": False
            }
        }
        
    async def check_service(self, name, config):
        """检查单个服务"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(config["url"], timeout=5.0)
                if response.status_code == 200:
                    return {
                        "name": name,
                        "status": "running",
                        "port": config["port"],
                        "response_time": response.elapsed.total_seconds(),
                        "critical": config["critical"]
                    }
        except:
            pass
        
        return {
            "name": name,
            "status": "stopped",
            "port": config["port"],
            "critical": config["critical"]
        }
    
    async def check_all_services(self):
        """检查所有服务"""
        tasks = []
        for name, config in self.services.items():
            tasks.append(self.check_service(name, config))
        return await asyncio.gather(*tasks)
    
    def check_system_resources(self):
        """检查系统资源"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "cores": psutil.cpu_count()
            },
            "memory": {
                "percent": memory.percent,
                "available_gb": memory.available / (1024**3),
                "total_gb": memory.total / (1024**3)
            },
            "disk": {
                "percent": disk.percent,
                "free_gb": disk.free / (1024**3),
                "total_gb": disk.total / (1024**3)
            }
        }
    
    def check_dependencies(self):
        """检查依赖"""
        deps = {
            "python3": "Python环境",
            "docker": "Docker容器",
            "ollama": "Ollama LLM",
            "go": "Go语言",
            "cargo": "Rust工具链"
        }
        
        results = {}
        for cmd, name in deps.items():
            try:
                subprocess.run([cmd, "--version"], capture_output=True, check=True)
                results[name] = "installed"
            except:
                results[name] = "missing"
        
        return results
    
    def generate_report(self, services, resources, dependencies):
        """生成健康报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_health": "healthy",
            "services": {},
            "resources": resources,
            "dependencies": dependencies,
            "issues": [],
            "recommendations": []
        }
        
        # 分析服务状态
        running_count = 0
        critical_down = []
        
        for service in services:
            report["services"][service["name"]] = service["status"]
            if service["status"] == "running":
                running_count += 1
            elif service["critical"]:
                critical_down.append(service["name"])
        
        # 判断整体健康度
        if critical_down:
            report["overall_health"] = "critical"
            report["issues"].append(f"关键服务未运行: {', '.join(critical_down)}")
            report["recommendations"].append("运行 'llm-control' 并选择 '1' 启动所有服务")
        elif running_count < len(services):
            report["overall_health"] = "degraded"
            report["issues"].append("部分服务未运行")
        
        # 检查资源
        if resources["cpu"]["percent"] > 80:
            report["issues"].append(f"CPU使用率过高: {resources['cpu']['percent']}%")
        
        if resources["memory"]["percent"] > 85:
            report["issues"].append(f"内存使用率过高: {resources['memory']['percent']}%")
            
        if resources["disk"]["free_gb"] < 5:
            report["issues"].append(f"磁盘空间不足: {resources['disk']['free_gb']:.1f}GB")
        
        # 检查依赖
        missing_deps = [k for k, v in dependencies.items() if v == "missing"]
        if missing_deps:
            report["issues"].append(f"缺少依赖: {', '.join(missing_deps)}")
            report["recommendations"].append("安装缺失的依赖")
        
        return report
    
    async def run(self):
        """运行健康检查"""
        print("🏥 本地LLM项目健康检查")
        print("=" * 50)
        
        # 检查服务
        print("\n检查服务状态...")
        services = await self.check_all_services()
        
        # 检查资源
        print("检查系统资源...")
        resources = self.check_system_resources()
        
        # 检查依赖
        print("检查依赖项...")
        dependencies = self.check_dependencies()
        
        # 生成报告
        report = self.generate_report(services, resources, dependencies)
        
        # 显示结果
        print("\n" + "=" * 50)
        print(f"总体健康状态: {report['overall_health'].upper()}")
        print("=" * 50)
        
        print("\n服务状态:")
        for name, status in report["services"].items():
            icon = "✅" if status == "running" else "❌"
            print(f"  {icon} {name}: {status}")
        
        print(f"\n系统资源:")
        print(f"  CPU: {resources['cpu']['percent']}% ({resources['cpu']['cores']} cores)")
        print(f"  内存: {resources['memory']['percent']}% ({resources['memory']['available_gb']:.1f}/{resources['memory']['total_gb']:.1f} GB)")
        print(f"  磁盘: {resources['disk']['percent']}% ({resources['disk']['free_gb']:.1f}/{resources['disk']['total_gb']:.1f} GB)")
        
        if report["issues"]:
            print(f"\n⚠️  发现的问题:")
            for issue in report["issues"]:
                print(f"  - {issue}")
        
        if report["recommendations"]:
            print(f"\n💡 建议:")
            for rec in report["recommendations"]:
                print(f"  - {rec}")
        
        # 保存报告
        report_file = self.project_home / f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 详细报告已保存到: {report_file}")
        
        return report

async def main():
    checker = HealthChecker()
    await checker.run()

if __name__ == "__main__":
    asyncio.run(main())
