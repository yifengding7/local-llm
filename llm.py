#!/usr/bin/env python3
"""
LLM项目控制台启动器
使用方法: python llm.py [命令]

命令:
    ui      - 打开Web UI控制面板（默认）
    start   - 启动所有服务
    stop    - 停止所有服务
    status  - 查看服务状态
"""

import os
import sys
import subprocess
import webbrowser
import argparse
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.absolute()

def open_ui():
    """打开UI控制面板"""
    print("🚀 正在启动LLM控制面板...")
    
    # 检查是否有HTML文件
    ui_files = [
        PROJECT_ROOT / "control_panel.html",
        PROJECT_ROOT / "control_panel_simple.html",
        PROJECT_ROOT / "index.html"
    ]
    
    ui_file = None
    for file in ui_files:
        if file.exists():
            ui_file = file
            break
    
    if ui_file:
        # 使用file://协议直接打开HTML文件
        file_url = f"file://{ui_file}"
        print(f"✨ 打开控制面板: {ui_file.name}")
        webbrowser.open(file_url)
        print("✅ 控制面板已在浏览器中打开！")
        print("💡 提示: 如果需要API功能，请先运行 'llm start' 启动后端服务")
    else:
        print("❌ 未找到UI文件")

def start_services():
    """启动所有服务"""
    print("🚀 启动所有LLM服务...")
    control_script = PROJECT_ROOT / "control_center.sh"
    
    if control_script.exists():
        subprocess.run(["bash", str(control_script), "start-all"])
    else:
        print("❌ 未找到control_center.sh")

def stop_services():
    """停止所有服务"""
    print("🛑 停止所有LLM服务...")
    control_script = PROJECT_ROOT / "control_center.sh"
    
    if control_script.exists():
        subprocess.run(["bash", str(control_script), "stop-all"])
    else:
        print("❌ 未找到control_center.sh")

def check_status():
    """检查服务状态"""
    print("🔍 检查LLM服务状态...")
    control_script = PROJECT_ROOT / "control_center.sh"
    
    if control_script.exists():
        subprocess.run(["bash", str(control_script), "status"])
    else:
        # 简单的状态检查
        print("\n📊 服务端口检查:")
        ports = {
            "8000": "AI监理系统 API",
            "11434": "Ollama LLM",
            "8080": "Weaviate向量数据库",
            "3001": "Go性能API",
            "6379": "Redis缓存"
        }
        
        for port, service in ports.items():
            result = subprocess.run(
                ["lsof", "-i", f":{port}"], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                print(f"✅ {service} (:{port}) - 运行中")
            else:
                print(f"❌ {service} (:{port}) - 未运行")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="LLM项目控制台",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python llm.py           # 打开UI控制面板（默认）
    python llm.py ui        # 打开UI控制面板
    python llm.py start     # 启动所有服务
    python llm.py stop      # 停止所有服务
    python llm.py status    # 查看服务状态
        """
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        default="ui",
        choices=["ui", "start", "stop", "status"],
        help="要执行的命令"
    )
    
    args = parser.parse_args()
    
    # ASCII艺术标题
    print("""
    ╔═══════════════════════════════════════╗
    ║     🤖 本地 LLM 项目控制台 v2.1      ║
    ╚═══════════════════════════════════════╝
    """)
    
    # 执行命令
    commands = {
        "ui": open_ui,
        "start": start_services,
        "stop": stop_services,
        "status": check_status
    }
    
    command_func = commands.get(args.command)
    if command_func:
        command_func()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
