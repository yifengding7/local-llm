#!/usr/bin/env python3
"""
Claude可以调用的MCP工具 - 通过终端执行Claude Code
"""

import subprocess
import time
import json
from pathlib import Path

def execute_claude_code(task: str, wait_seconds: int = 3) -> dict:
    """
    通过终端执行Claude Code任务
    
    参数:
    - task: 要执行的任务描述
    - wait_seconds: 等待执行完成的秒数
    
    返回:
    - 执行结果的字典
    """
    
    # 创建输出目录
    output_dir = Path.home() / "claude-code-output"
    output_dir.mkdir(exist_ok=True)
    
    # 创建临时输出文件
    timestamp = int(time.time())
    output_file = output_dir / f"output_{timestamp}.json"
    
    # 构建AppleScript命令
    # 转义单引号
    escaped_task = task.replace("'", "\\'")
    
    applescript = f'''
    tell application "Terminal"
        do script "cd {output_dir} && python3 ~/.local/bin/claude '{escaped_task}' > {output_file} 2>&1"
    end tell
    '''
    
    try:
        # 执行AppleScript
        subprocess.run(["osascript", "-e", applescript], check=True)
        
        # 等待命令执行
        time.sleep(wait_seconds)
        
        # 尝试读取输出
        if output_file.exists():
            try:
                # 尝试解析JSON
                with open(output_file) as f:
                    result = json.load(f)
                
                # 删除临时文件
                output_file.unlink()
                
                return {
                    "success": True,
                    "result": result,
                    "output_dir": str(output_dir)
                }
            except json.JSONDecodeError:
                # 如果不是JSON，返回原始内容
                content = output_file.read_text()
                output_file.unlink()
                
                return {
                    "success": True,
                    "raw_output": content,
                    "output_dir": str(output_dir)
                }
        else:
            return {
                "success": False,
                "error": "No output file created",
                "message": "Command may still be running or failed"
            }
            
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "error": "Failed to execute AppleScript",
            "details": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": "Unexpected error",
            "details": str(e),
            "type": type(e).__name__
        }


def create_project_with_claude(project_name: str, project_type: str = "Python") -> dict:
    """使用Claude Code创建项目"""
    task = f"create a {project_type} project named {project_name}"
    return execute_claude_code(task, wait_seconds=5)


def analyze_code_with_claude(file_path: str) -> dict:
    """使用Claude Code分析代码"""
    task = f"analyze the code in {file_path} and provide suggestions"
    return execute_claude_code(task, wait_seconds=5)


def write_code_with_claude(description: str, language: str = "Python") -> dict:
    """使用Claude Code编写代码"""
    task = f"write {language} code that {description}"
    return execute_claude_code(task, wait_seconds=5)


# 测试函数
if __name__ == "__main__":
    print("🧪 测试Claude Code MCP工具...")
    
    # 测试1: 创建项目
    print("\n1. 创建项目测试:")
    result = create_project_with_claude("test-mcp-project", "Python")
    print(json.dumps(result, indent=2))
    
    # 测试2: 写代码
    print("\n2. 写代码测试:")
    result = write_code_with_claude("implements a fibonacci sequence generator")
    print(json.dumps(result, indent=2))
