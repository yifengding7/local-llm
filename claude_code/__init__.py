"""
Claude Code 集成模块
统一的Claude AI代码生成和分析工具
"""

__version__ = "2.2.0"
__author__ = "Claude Code Assistant"

from .claude_simulator import ClaudeSimulator
from .mcp_tools.executor import MCPExecutor
from .mcp_tools.bridge import TerminalBridge

__all__ = [
    "ClaudeSimulator",
    "MCPExecutor", 
    "TerminalBridge"
]