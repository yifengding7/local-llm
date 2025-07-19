#!/usr/bin/env python3
"""
AI监理系统 - 安装诊断工具
检查系统环境并提供修复建议
"""

import sys
import subprocess
import platform
import os
import json
import shutil

class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def run_command(cmd):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def check_system():
    """检查系统信息"""
    print(f"\n{Color.BLUE}=== 系统信息 ==={Color.END}")
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"Python版本: {sys.version}")
    print(f"架构: {platform.machine()}")

def check_python():
    """检查Python环境"""
    print(f"\n{Color.BLUE}=== Python环境检查 ==={Color.END}")
    
    # 检查Python版本
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"{Color.GREEN}✓ Python版本正常: {version.major}.{version.minor}.{version.micro}{Color.END}")
    else:
        print(f"{Color.RED}✗ Python版本过低，需要3.9+{Color.END}")
        print(f"  建议: brew install python@3.11")
    
    # 检查pip
    success, out, _ = run_command("pip --version")
    if success:
        print(f"{Color.GREEN}✓ pip已安装: {out}{Color.END}")
    else:
        print(f"{Color.RED}✗ pip未安装{Color.END}")
    
    # 检查虚拟环境
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print(f"{Color.GREEN}✓ 当前在虚拟环境中{Color.END}")
    else:
        print(f"{Color.YELLOW}! 建议使用虚拟环境{Color.END}")
        print(f"  创建: python3 -m venv venv")
        print(f"  激活: source venv/bin/activate")

def check_dependencies():
    """检查关键依赖"""
    print(f"\n{Color.BLUE}=== 依赖检查 ==={Color.END}")
    
    dependencies = {
        "brew": "Homebrew包管理器",
        "docker": "Docker容器",
        "ollama": "Ollama LLM运行时",
        "git": "Git版本控制"
    }
    
    for cmd, name in dependencies.items():
        success, version, _ = run_command(f"{cmd} --version 2>/dev/null || {cmd} -v 2>/dev/null")
        if success:
            print(f"{Color.GREEN}✓ {name}已安装{Color.END}")
        else:
            print(f"{Color.RED}✗ {name}未安装{Color.END}")
            if cmd == "brew":
                print(f"  安装: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
            else:
                print(f"  安装: brew install {cmd}")

def check_python_packages():
    """检查Python包"""
    print(f"\n{Color.BLUE}=== Python包检查 ==={Color.END}")
    
    required_packages = {
        "fastapi": "0.111.0",
        "uvicorn": "0.30.1",
        "pydantic": "2.7.4",
        "httpx": "0.27.0",
        "ollama": "0.3.0"
    }
    
    for package, version in required_packages.items():
        try:
            __import__(package)
            print(f"{Color.GREEN}✓ {package}已安装{Color.END}")
        except ImportError:
            print(f"{Color.RED}✗ {package}未安装{Color.END}")
            print(f"  安装: pip install {package}=={version}")

def check_ollama():
    """检查Ollama服务"""
    print(f"\n{Color.BLUE}=== Ollama检查 ==={Color.END}")
    
    # 检查Ollama服务
    success, _, _ = run_command("curl -s http://localhost:11434/api/tags")
    if success:
        print(f"{Color.GREEN}✓ Ollama服务运行中{Color.END}")
        
        # 检查模型
        success, out, _ = run_command("ollama list")
        if success and out:
            print(f"{Color.GREEN}✓ 已安装模型:{Color.END}")
            for line in out.split('\n')[1:]:  # 跳过标题行
                if line.strip():
                    print(f"  - {line.split()[0]}")
        else:
            print(f"{Color.YELLOW}! 没有安装模型{Color.END}")
            print(f"  推荐模型:")
            print(f"  - ollama pull llama3.2")
            print(f"  - ollama pull qwen2.5-coder:1.5b")
            print(f"  - ollama pull phi3:mini")
    else:
        print(f"{Color.RED}✗ Ollama服务未运行{Color.END}")
        print(f"  启动: ollama serve")

def check_ports():
    """检查端口占用"""
    print(f"\n{Color.BLUE}=== 端口检查 ==={Color.END}")
    
    ports = {
        8000: "API服务",
        11434: "Ollama",
        6379: "Redis",
        8080: "Weaviate"
    }
    
    for port, service in ports.items():
        success, out, _ = run_command(f"lsof -i :{port} 2>/dev/null | grep LISTEN")
        if success and out:
            print(f"{Color.YELLOW}! 端口{port}已被占用 ({service}){Color.END}")
            print(f"  {out.split()[0]}")
        else:
            print(f"{Color.GREEN}✓ 端口{port}可用 ({service}){Color.END}")

def suggest_fixes():
    """提供修复建议"""
    print(f"\n{Color.BLUE}=== 推荐安装流程 ==={Color.END}")
    print("1. 安装基础工具:")
    print("   brew install python@3.11 ollama git")
    print("")
    print("2. 创建项目:")
    print("   mkdir -p ~/ai-monitor-local")
    print("   cd ~/ai-monitor-local")
    print("   python3.11 -m venv venv")
    print("   source venv/bin/activate")
    print("")
    print("3. 安装依赖:")
    print("   pip install fastapi uvicorn httpx ollama")
    print("")
    print("4. 启动Ollama:")
    print("   ollama serve")
    print("")
    print("5. 下载模型:")
    print("   ollama pull llama3.2")
    print("")
    print("6. 运行快速安装:")
    print("   bash quick_install.sh")

def main():
    print(f"{Color.BLUE}AI监理系统 - 环境诊断工具{Color.END}")
    print("=" * 40)
    
    check_system()
    check_python()
    check_dependencies()
    check_python_packages()
    check_ollama()
    check_ports()
    suggest_fixes()
    
    print(f"\n{Color.GREEN}诊断完成！{Color.END}")

if __name__ == "__main__":
    main()
