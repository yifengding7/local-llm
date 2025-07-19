#!/usr/bin/env python3
"""
Claude Code MCP包装器
允许Claude通过MCP协议调用Claude Code
"""

import subprocess
import json
import tempfile
import os
import time
from typing import Dict, Any, Optional
from pathlib import Path

class ClaudeCodeMCP:
    """Claude Code的MCP包装器"""
    
    def __init__(self):
        self.claude_cmd = self._find_claude_command()
        self.workspace = Path.home() / "claude-code-workspace"
        self.workspace.mkdir(exist_ok=True)
        
    def _find_claude_command(self) -> Optional[str]:
        """查找Claude Code命令"""
        possible_commands = ["claude", "claude-code", "claude-dev"]
        
        for cmd in possible_commands:
            try:
                result = subprocess.run(
                    ["which", cmd],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except:
                continue
        
        # 检查常见安装位置
        common_paths = [
            "/usr/local/bin/claude",
            "/opt/homebrew/bin/claude",
            "~/.local/bin/claude"
        ]
        
        for path in common_paths:
            expanded_path = os.path.expanduser(path)
            if os.path.exists(expanded_path):
                return expanded_path
        
        return None
    
    def execute_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行Claude Code任务"""
        if not self.claude_cmd:
            return {
                "status": "error",
                "message": "Claude Code未安装",
                "suggestion": "请先安装Claude Code: https://claude.ai/code"
            }
        
        # 创建临时任务文件
        task_file = self.workspace / f"task_{int(time.time())}.md"
        
        # 构建任务内容
        task_content = f"# Claude Code Task\n\n{task}\n"
        
        if context:
            task_content += "\n## Context\n"
            for key, value in context.items():
                task_content += f"- **{key}**: {value}\n"
        
        # 写入任务文件
        task_file.write_text(task_content)
        
        try:
            # 构建Claude Code命令
            cmd = [
                self.claude_cmd,
                "--task", str(task_file),
                "--output", str(self.workspace),
                "--auto-approve",  # 自动批准操作
                "--json"  # JSON输出格式
            ]
            
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.workspace)
            )
            
            if result.returncode == 0:
                # 尝试解析JSON输出
                try:
                    output = json.loads(result.stdout)
                    return {
                        "status": "success",
                        "output": output,
                        "files_created": self._list_created_files()
                    }
                except json.JSONDecodeError:
                    return {
                        "status": "success",
                        "output": result.stdout,
                        "raw_output": True
                    }
            else:
                return {
                    "status": "error",
                    "error": result.stderr,
                    "stdout": result.stdout
                }
                
        except Exception as e:
            return {
                "status": "error",
                "exception": str(e),
                "type": type(e).__name__
            }
        finally:
            # 清理任务文件
            if task_file.exists():
                task_file.unlink()
    
    def _list_created_files(self) -> list:
        """列出最近创建的文件"""
        files = []
        cutoff_time = time.time() - 300  # 5分钟内的文件
        
        for file_path in self.workspace.rglob("*"):
            if file_path.is_file() and file_path.stat().st_mtime > cutoff_time:
                files.append(str(file_path.relative_to(self.workspace)))
        
        return files
    
    def create_project(self, project_name: str, project_type: str, requirements: str) -> Dict[str, Any]:
        """创建项目"""
        task = f"""
        Create a new {project_type} project named "{project_name}"
        
        Requirements:
        {requirements}
        
        Please include:
        - Complete project structure
        - All necessary configuration files
        - Basic implementation
        - README with setup instructions
        """
        
        return self.execute_task(task, {
            "project_type": project_type,
            "project_name": project_name
        })
    
    def analyze_code(self, file_path: str, analysis_type: str = "full") -> Dict[str, Any]:
        """分析代码"""
        task = f"""
        Analyze the code at: {file_path}
        
        Analysis type: {analysis_type}
        
        Please provide:
        - Code quality assessment
        - Potential bugs or issues
        - Performance considerations
        - Improvement suggestions
        """
        
        return self.execute_task(task, {
            "file_path": file_path,
            "analysis_type": analysis_type
        })
    
    def refactor_code(self, file_path: str, refactor_goals: str) -> Dict[str, Any]:
        """重构代码"""
        task = f"""
        Refactor the code at: {file_path}
        
        Refactoring goals:
        {refactor_goals}
        
        Please:
        - Maintain functionality
        - Improve code quality
        - Add appropriate comments
        - Update tests if present
        """
        
        return self.execute_task(task, {
            "file_path": file_path,
            "refactor_type": "guided"
        })
    
    def batch_process(self, files: list, operation: str) -> Dict[str, Any]:
        """批量处理文件"""
        task = f"""
        Perform batch operation on the following files:
        
        Files:
        {chr(10).join(f'- {f}' for f in files)}
        
        Operation: {operation}
        
        Please process all files consistently.
        """
        
        return self.execute_task(task, {
            "file_count": len(files),
            "operation": operation
        })


# MCP工具接口函数
def claude_code_create_project(project_name: str, project_type: str, requirements: str) -> Dict[str, Any]:
    """通过Claude Code创建项目"""
    mcp = ClaudeCodeMCP()
    return mcp.create_project(project_name, project_type, requirements)

def claude_code_analyze(file_path: str, analysis_type: str = "full") -> Dict[str, Any]:
    """通过Claude Code分析代码"""
    mcp = ClaudeCodeMCP()
    return mcp.analyze_code(file_path, analysis_type)

def claude_code_refactor(file_path: str, goals: str) -> Dict[str, Any]:
    """通过Claude Code重构代码"""
    mcp = ClaudeCodeMCP()
    return mcp.refactor_code(file_path, goals)

def claude_code_batch(files: list, operation: str) -> Dict[str, Any]:
    """通过Claude Code批量处理"""
    mcp = ClaudeCodeMCP()
    return mcp.batch_process(files, operation)

def claude_code_execute(task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """通过Claude Code执行自定义任务"""
    mcp = ClaudeCodeMCP()
    return mcp.execute_task(task, context)


# 命令行测试
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Claude Code MCP包装器")
    parser.add_argument("command", choices=["test", "create", "analyze"])
    parser.add_argument("--name", help="项目名称")
    parser.add_argument("--type", help="项目类型")
    parser.add_argument("--file", help="文件路径")
    
    args = parser.parse_args()
    
    mcp = ClaudeCodeMCP()
    
    if args.command == "test":
        print("🔍 检查Claude Code...")
        if mcp.claude_cmd:
            print(f"✅ 找到Claude Code: {mcp.claude_cmd}")
        else:
            print("❌ Claude Code未安装")
            print("📦 安装说明: https://claude.ai/code")
    
    elif args.command == "create" and args.name and args.type:
        print(f"🚀 创建{args.type}项目: {args.name}")
        result = mcp.create_project(args.name, args.type, "Basic project setup")
        print(json.dumps(result, indent=2))
    
    elif args.command == "analyze" and args.file:
        print(f"🔍 分析文件: {args.file}")
        result = mcp.analyze_code(args.file)
        print(json.dumps(result, indent=2))
