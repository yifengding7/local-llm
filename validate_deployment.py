#!/usr/bin/env python3
"""
AI监理系统 v2.1 - 完整部署验证脚本
验证所有服务是否正常运行
"""

import asyncio
import httpx
import subprocess
import time
import sys
import os
from datetime import datetime

class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

async def check_service(name, url, expected_status=200):
    """检查单个服务状态"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
            if response.status_code == expected_status:
                return True, f"{Color.GREEN}✅ {name} 运行正常{Color.END} ({url})"
            else:
                return False, f"{Color.YELLOW}⚠️  {name} 响应异常{Color.END} (状态码: {response.status_code})"
    except Exception as e:
        return False, f"{Color.RED}❌ {name} 未运行{Color.END} ({type(e).__name__})"

async def check_all_services():
    """检查所有服务状态"""
    print(f"\n{Color.BLUE}{Color.BOLD}🔍 AI监理系统 v2.1 - 服务状态检查{Color.END}")
    print("=" * 60)
    
    services = [
        ("核心Python服务", "http://localhost:8000/health"),
        ("核心状态API", "http://localhost:8000/status"),
        ("Ollama LLM引擎", "http://localhost:11434/api/tags"),
        ("Weaviate向量数据库", "http://localhost:8080/v1/meta"),
        ("Go闪电API", "http://localhost:3001/health"),
        ("Rust零延迟引擎", "http://localhost:3002/health"),
    ]
    
    results = []
    for name, url in services:
        success, message = await check_service(name, url)
        results.append((name, success))
        print(message)
    
    return results

def check_process(process_name):
    """检查进程是否运行"""
    try:
        result = subprocess.run(['pgrep', '-f', process_name], capture_output=True)
        return result.returncode == 0
    except:
        return False

def compile_and_start_services():
    """编译并启动未运行的服务"""
    print(f"\n{Color.PURPLE}{Color.BOLD}🔧 启动未运行的服务...{Color.END}")
    
    # 检查并启动Go服务
    if not check_process("main.*3001"):
        print(f"{Color.CYAN}正在启动Go闪电API...{Color.END}")
        go_dir = "/Users/imac/Documents/编程/项目/本地llm项目/ai-monitor-v2/performance/go"
        if os.path.exists(go_dir):
            subprocess.Popen(
                ["sh", "-c", f"cd {go_dir} && go mod tidy && go run main.go > ../../logs/go-api.log 2>&1 &"],
                shell=False
            )
            time.sleep(3)
    
    # 检查并编译Rust服务
    if not check_process("ai-monitor-rust"):
        print(f"{Color.CYAN}正在编译并启动Rust零延迟引擎...{Color.END}")
        rust_dir = "/Users/imac/Documents/编程/项目/本地llm项目/ai-monitor-v2/performance/rust"
        if os.path.exists(rust_dir):
            subprocess.Popen(
                ["sh", "-c", f"cd {rust_dir} && cargo build --release && ./target/release/ai-monitor-rust > ../../logs/rust-engine.log 2>&1 &"],
                shell=False
            )
            print("⏳ Rust编译需要几分钟，请稍候...")
            time.sleep(5)

async def test_api_functionality():
    """测试API功能"""
    print(f"\n{Color.BLUE}{Color.BOLD}🧪 测试API功能...{Color.END}")
    
    # 测试核心服务健康检查
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                data = response.json()
                print(f"{Color.GREEN}✅ 核心服务响应:{Color.END}")
                print(f"   - 状态: {data.get('status')}")
                print(f"   - 版本: {data.get('version')}")
                print(f"   - 运行时间: {data.get('uptime')}秒")
    except Exception as e:
        print(f"{Color.RED}❌ 核心服务测试失败: {e}{Color.END}")
    
    # 测试Ollama模型
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                print(f"{Color.GREEN}✅ Ollama模型:{Color.END}")
                for model in models:
                    print(f"   - {model['name']} ({model['size'] / 1e9:.1f}GB)")
    except Exception as e:
        print(f"{Color.RED}❌ Ollama测试失败: {e}{Color.END}")

def generate_final_report(results):
    """生成最终报告"""
    print(f"\n{Color.BOLD}{'='*60}{Color.END}")
    print(f"{Color.BLUE}{Color.BOLD}📊 部署验证报告{Color.END}")
    print(f"{Color.BOLD}{'='*60}{Color.END}")
    
    total = len(results)
    running = sum(1 for _, success in results if success)
    
    print(f"\n服务状态汇总:")
    print(f"- 总服务数: {total}")
    print(f"- 运行中: {Color.GREEN}{running}{Color.END}")
    print(f"- 未运行: {Color.RED}{total - running}{Color.END}")
    
    completion_rate = (running / total) * 100
    print(f"\n部署完成度: {Color.BOLD}{completion_rate:.1f}%{Color.END}")
    
    if completion_rate == 100:
        print(f"\n{Color.GREEN}{Color.BOLD}🎉 恭喜！AI监理系统 v2.1 已100%部署完成！{Color.END}")
        print("\n可用的服务端点:")
        print("- 核心API: http://localhost:8000")
        print("- API文档: http://localhost:8000/docs")
        print("- Ollama: http://localhost:11434")
        print("- Weaviate: http://localhost:8080")
        print("- Go API: http://localhost:3001")
        print("- Rust引擎: http://localhost:3002")
    elif completion_rate >= 80:
        print(f"\n{Color.YELLOW}{Color.BOLD}⚠️  系统基本部署完成，部分高级功能可能不可用。{Color.END}")
    else:
        print(f"\n{Color.RED}{Color.BOLD}❌ 部署未完成，请检查错误并重试。{Color.END}")
    
    # 保存报告
    report_file = f"deployment_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w') as f:
        f.write(f"AI监理系统 v2.1 部署验证报告\n")
        f.write(f"时间: {datetime.now()}\n")
        f.write(f"完成度: {completion_rate:.1f}%\n\n")
        for name, success in results:
            f.write(f"{name}: {'✅ 运行中' if success else '❌ 未运行'}\n")
    
    print(f"\n报告已保存到: {report_file}")

async def main():
    """主函数"""
    print(f"{Color.PURPLE}{Color.BOLD}🚀 AI监理系统 v2.1 - 完整部署验证{Color.END}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 第一次检查
    results = await check_all_services()
    
    # 如果有服务未运行，尝试启动
    if any(not success for _, success in results):
        compile_and_start_services()
        print(f"\n{Color.YELLOW}⏳ 等待服务启动...{Color.END}")
        await asyncio.sleep(10)
        
        # 第二次检查
        print(f"\n{Color.BLUE}{Color.BOLD}🔄 重新检查服务状态...{Color.END}")
        results = await check_all_services()
    
    # 测试API功能
    await test_api_functionality()
    
    # 生成最终报告
    generate_final_report(results)

if __name__ == "__main__":
    asyncio.run(main())
