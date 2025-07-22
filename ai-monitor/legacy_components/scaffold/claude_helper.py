#!/bin/bash
# Claude Assistant Helper - 让Claude更容易调用这些工具

# 定义项目目录
PROJECT_DIR="/Users/imac/Documents/编程/项目/本地llm项目"
OUTPUT_DIR="$HOME/claude-code-output"

# 创建必要的目录
mkdir -p "$OUTPUT_DIR"
mkdir -p "$HOME/.claude-assistant"

# 功能1: 创建项目
claude_create_project() {
    local project_name=$1
    local project_type=${2:-"Python"}
    
    echo "🚀 Creating $project_type project: $project_name"
    python3 "$PROJECT_DIR/claude_simulator.py" "create a $project_type project named $project_name"
}

# 功能2: 分析代码
claude_analyze() {
    local file_path=$1
    echo "🔍 Analyzing: $file_path"
    python3 "$PROJECT_DIR/claude_simulator.py" "analyze the code in $file_path"
}

# 功能3: 写代码
claude_write() {
    local description="$@"
    echo "✍️ Writing code: $description"
    python3 "$PROJECT_DIR/claude_simulator.py" "write code that $description"
}

# 功能4: 批量处理
claude_batch() {
    local operation=$1
    local pattern=$2
    echo "🔄 Batch operation: $operation on $pattern"
    python3 "$PROJECT_DIR/claude_simulator.py" "batch $operation all files matching $pattern"
}

# 功能5: 运行MCP工具测试
claude_test() {
    echo "🧪 Testing Claude Code integration..."
    python3 "$PROJECT_DIR/claude_code_mcp_tool.py"
}

# 主命令处理
case "$1" in
    create)
        claude_create_project "$2" "$3"
        ;;
    analyze)
        claude_analyze "$2"
        ;;
    write)
        shift
        claude_write "$@"
        ;;
    batch)
        claude_batch "$2" "$3"
        ;;
    test)
        claude_test
        ;;
    *)
        echo "Claude Assistant Helper"
        echo "Usage:"
        echo "  $0 create <project-name> [type]     - Create a new project"
        echo "  $0 analyze <file-path>              - Analyze code file"
        echo "  $0 write <description>              - Write code"
        echo "  $0 batch <operation> <pattern>      - Batch process files"
        echo "  $0 test                             - Test integration"
        echo ""
        echo "Examples:"
        echo "  $0 create my-api FastAPI"
        echo "  $0 analyze /path/to/code.py"
        echo "  $0 write a fibonacci generator"
        echo "  $0 batch refactor '*.py'"
        ;;
esac
