#!/usr/bin/env python3
"""
Claude Terminal Bridge - 通过终端调用Claude Code
"""

import subprocess
import time
import os
import json
from pathlib import Path

class ClaudeTerminalBridge:
    def __init__(self):
        self.temp_dir = Path.home() / ".claude-bridge"
        self.temp_dir.mkdir(exist_ok=True)
        
    def call_claude_code(self, prompt: str, wait_time: int = 5) -> str:
        """通过终端调用Claude Code"""
        
        # 创建临时文件存储prompt
        prompt_file = self.temp_dir / f"prompt_{int(time.time())}.txt"
        output_file = self.temp_dir / f"output_{int(time.time())}.txt"
        
        # 写入prompt
        prompt_file.write_text(prompt)
        
        # 构建AppleScript命令
        applescript = f'''
        tell application "Terminal"
            -- 创建新标签页执行Claude Code
            do script "claude '{prompt}' > '{output_file}' 2>&1 && echo 'DONE' >> '{output_file}'"
        end tell
        '''
        
        # 执行AppleScript
        try:
            subprocess.run(["osascript", "-e", applescript], check=True)
            
            # 等待命令完成
            time.sleep(wait_time)
            
            # 检查输出
            if output_file.exists():
                result = output_file.read_text()
                
                # 清理临时文件
                prompt_file.unlink()
                output_file.unlink()
                
                return result
            else:
                return "Error: No output file created"
                
        except subprocess.CalledProcessError as e:
            return f"Error executing AppleScript: {e}"
        except Exception as e:
            return f"Unexpected error: {e}"
    
    def create_code_task(self, task_type: str, details: dict) -> str:
        """创建代码任务并通过终端执行"""
        
        # 根据任务类型构建prompt
        if task_type == "create_file":
            prompt = f"Create a {details.get('language', 'Python')} file named {details.get('filename')} with the following content: {details.get('content')}"
        
        elif task_type == "analyze":
            prompt = f"Analyze the code in {details.get('file_path')} and provide improvement suggestions"
        
        elif task_type == "refactor":
            prompt = f"Refactor the code in {details.get('file_path')} to {details.get('goal')}"
        
        elif task_type == "create_project":
            prompt = f"Create a new {details.get('project_type')} project named {details.get('project_name')} with {details.get('features')}"
        
        else:
            prompt = details.get('custom_prompt', 'Help me write code')
        
        return self.call_claude_code(prompt)


# 简单的通过osascript直接调用
def quick_claude_code(prompt: str):
    """快速调用Claude Code"""
    applescript = f'''
    tell application "Terminal"
        do script "echo '{prompt}' | claude"
    end tell
    '''
    
    subprocess.run(["osascript", "-e", applescript])
    return "Command sent to terminal"


# 测试函数
def test_claude_code_integration():
    """测试Claude Code集成"""
    print("🧪 测试Claude Code集成...")
    
    # 测试1: 检查Claude是否安装
    test_script = '''
    tell application "Terminal"
        do script "which claude || echo 'Claude Code not found'"
    end tell
    '''
    
    subprocess.run(["osascript", "-e", test_script])
    time.sleep(2)
    
    print("✅ 测试命令已发送到终端")
    

if __name__ == "__main__":
    # 运行测试
    test_claude_code_integration()
