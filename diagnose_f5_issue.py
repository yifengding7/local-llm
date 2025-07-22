#!/usr/bin/env python3
"""
F5录音键失效诊断工具
诊断进入本地LLM项目后F5键无法使用的问题
"""

import subprocess
import os
import signal
import psutil
import time
from datetime import datetime

def run_command(cmd):
    """运行shell命令并返回输出"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def check_audio_devices():
    """检查音频设备状态"""
    print("\n🎤 音频设备检查:")
    print("-" * 50)
    
    # 列出音频输入设备
    cmd = "system_profiler SPAudioDataType | grep -A2 'Input Devices:'"
    result = run_command(cmd)
    print("音频输入设备:")
    print(result)
    
    # 检查音频服务状态
    print("\n音频服务状态:")
    audio_processes = ["coreaudiod", "audio", "AVAudioSession"]
    for proc in audio_processes:
        cmd = f"ps aux | grep -i {proc} | grep -v grep"
        result = run_command(cmd)
        if result:
            print(f"{proc}: 运行中")
            print(result[:200] + "..." if len(result) > 200 else result)

def check_port_usage():
    """检查端口占用情况"""
    print("\n🔌 端口占用检查:")
    print("-" * 50)
    
    # 检查常见的音频相关端口
    audio_ports = [
        (5000, "AirPlay/音频流"),
        (5005, "控制面板"),
        (8000, "FastAPI"),
        (8080, "Weaviate"),
        (11434, "Ollama"),
        (50000, "音频服务"),
        (50001, "音频服务"),
    ]
    
    for port, desc in audio_ports:
        cmd = f"lsof -i :{port} 2>/dev/null | grep LISTEN"
        result = run_command(cmd)
        if result:
            print(f"端口 {port} ({desc}): 被占用")
            print(f"  {result[:100]}...")
        else:
            print(f"端口 {port} ({desc}): 空闲")

def check_keyboard_hooks():
    """检查键盘钩子和快捷键绑定"""
    print("\n⌨️ 键盘监听检查:")
    print("-" * 50)
    
    # 检查辅助功能权限
    print("辅助功能权限状态:")
    cmd = "tccutil -l | grep -i 'accessibility'"
    result = run_command(cmd)
    print(result if result else "未找到特殊权限")
    
    # 检查系统快捷键
    print("\n系统快捷键设置:")
    cmd = "defaults read com.apple.symbolichotkeys | grep -A5 'F5'"
    result = run_command(cmd)
    print(result if result else "F5键未被系统快捷键占用")

def check_python_processes():
    """检查Python进程"""
    print("\n🐍 Python进程检查:")
    print("-" * 50)
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'llm' in cmdline.lower() or 'monitor' in cmdline.lower():
                    print(f"\nPID: {proc.info['pid']}")
                    print(f"命令: {cmdline[:200]}...")
                    
                    # 检查打开的文件描述符
                    try:
                        files = proc.open_files()
                        audio_files = [f for f in files if 'audio' in f.path.lower() or 'sound' in f.path.lower()]
                        if audio_files:
                            print("⚠️ 发现音频相关文件:")
                            for f in audio_files:
                                print(f"  - {f.path}")
                    except:
                        pass
                    
                    # 检查网络连接
                    try:
                        connections = proc.connections()
                        if connections:
                            print(f"网络连接数: {len(connections)}")
                    except:
                        pass
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

def check_docker_containers():
    """检查Docker容器"""
    print("\n🐳 Docker容器检查:")
    print("-" * 50)
    
    cmd = "docker ps --format 'table {{.Names}}\t{{.Ports}}\t{{.Status}}'"
    result = run_command(cmd)
    print(result if result else "没有运行中的Docker容器")

def check_system_logs():
    """检查系统日志中的音频错误"""
    print("\n📋 系统日志检查 (最近的音频相关条目):")
    print("-" * 50)
    
    # 检查最近的音频相关系统日志
    cmd = "log show --predicate 'subsystem == \"com.apple.audio\"' --last 1m 2>/dev/null | tail -20"
    result = run_command(cmd)
    if result:
        print("音频子系统日志:")
        print(result)
    
    # 检查辅助功能日志
    cmd = "log show --predicate 'process == \"AXUIServer\"' --last 1m 2>/dev/null | grep -i 'dictation\\|speech' | tail -10"
    result = run_command(cmd)
    if result:
        print("\n语音识别相关日志:")
        print(result)

def kill_audio_blocking_processes():
    """终止可能阻塞音频的进程"""
    print("\n🔧 修复建议:")
    print("-" * 50)
    
    suggestions = []
    
    # 检查是否有Python进程占用音频
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if any(keyword in cmdline.lower() for keyword in ['audio', 'speech', 'voice', 'sound']):
                    suggestions.append(f"发现可疑进程 (PID: {proc.info['pid']}): {cmdline[:100]}")
                    suggestions.append(f"  建议终止: kill {proc.info['pid']}")
        except:
            continue
    
    if not suggestions:
        suggestions.append("1. 尝试重启音频服务:")
        suggestions.append("   sudo killall coreaudiod")
        suggestions.append("\n2. 检查系统偏好设置:")
        suggestions.append("   系统偏好设置 > 键盘 > 快捷键 > 听写")
        suggestions.append("   确保F5没有被其他功能占用")
        suggestions.append("\n3. 重置语音识别:")
        suggestions.append("   系统偏好设置 > 键盘 > 听写 > 关闭再打开")
        suggestions.append("\n4. 检查Docker容器:")
        suggestions.append("   docker compose down")
        suggestions.append("   docker compose up -d")
        suggestions.append("\n5. 重启控制中心:")
        suggestions.append("   ./control_center.sh stop")
        suggestions.append("   ./control_center.sh start")
    
    for suggestion in suggestions:
        print(suggestion)

def main():
    """主诊断流程"""
    print("=" * 60)
    print("🔍 F5录音键失效诊断工具")
    print(f"⏰ 诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 运行各项检查
    check_audio_devices()
    check_port_usage()
    check_keyboard_hooks()
    check_python_processes()
    check_docker_containers()
    check_system_logs()
    kill_audio_blocking_processes()
    
    print("\n" + "=" * 60)
    print("诊断完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
