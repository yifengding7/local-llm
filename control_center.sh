#!/bin/bash
# CCIS & AI Monitor Control Center - 综合控制中心
# 一个命令管理整个本地LLM项目

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[0;37m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# 系统路径
PROJECT_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
AI_MONITOR_HOME="$PROJECT_HOME/ai-monitor"
OUTPUT_DIR="$HOME/claude-code-output"
LOGS_DIR="$PROJECT_HOME/monitoring/logs"

# PID文件位置
PID_DIR="$PROJECT_HOME/.pids"
mkdir -p "$PID_DIR"

# 清屏函数
clear_screen() {
    clear
}

# 打印Logo
print_logo() {
    echo -e "${CYAN}${BOLD}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║          🚀 本地LLM项目控制中心 Control Center 🚀             ║"
    echo "╟───────────────────────────────────────────────────────────────╢"
    echo "║  AI监理系统 v2.2 (Modernized) + CCIS                          ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 检查服务状态
check_service_status() {
    local port=$1
    local service_name=$2
    
    if lsof -i :$port > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 运行中${NC}"
    else
        echo -e "${RED}❌ 未运行${NC}"
    fi
}

# 显示服务状态
show_status() {
    clear_screen
    print_logo
    echo -e "\n${BLUE}${BOLD}📊 服务状态监控${NC}\n"
    
    echo -e "1. ${CYAN}FastAPI 服务${NC} (8000): $(check_service_status 8000 'FastAPI 服务')"
    echo -e "2. ${CYAN}Ollama LLM引擎${NC} (11434): $(check_service_status 11434 'Ollama')"
    echo -e "3. ${CYAN}Weaviate向量库${NC} (8080): $(check_service_status 8080 'Weaviate')"
    
    echo -e "\n${YELLOW}系统资源使用:${NC}"
    echo -e "CPU: $(top -l 1 | grep "CPU usage" | awk '{print $3}') used"
    echo -e "内存: $(top -l 1 | grep PhysMem | awk '{print $2, $4}')"
    
    echo -e "\n按任意键返回主菜单..."
    read -n 1
}

# 启动AI监理系统核心服务 (Poetry)
start_api_dev() {
    echo -e "${YELLOW}启动FastAPI服务 (开发模式)...${NC}"
    
    if ! lsof -i :8000 > /dev/null 2>&1; then
        echo "启动中..."
        poetry run uvicorn ai_monitor.core.main:app --reload --host 0.0.0.0 --port 8000 > "$LOGS_DIR/api-dev.log" 2>&1 &
        echo $! > "$PID_DIR/api-dev.pid"
        sleep 3
        echo -e "${GREEN}✅ FastAPI服务已在开发模式下启动${NC}"
    else
        echo -e "${YELLOW}⚠️ FastAPI服务已在运行${NC}"
    fi
    echo -e "\n按任意键返回主菜单..."
    read -n 1
}

# 启动Docker服务栈
start_docker_stack() {
    echo -e "${YELLOW}启动Docker服务栈 (API + Ollama + Weaviate)...${NC}"
    docker compose up -d
    echo -e "${GREEN}✅ Docker服务栈已启动${NC}"
    echo -e "\n按任意键返回主菜单..."
    read -n 1
}


# 启动所有服务
start_all_services() {
    clear_screen
    print_logo
    echo -e "\n${BLUE}${BOLD}🚀 启动所有服务 (Docker Compose)${NC}\n"
    start_docker_stack
}

# 停止服务函数
stop_service() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if kill -0 $pid 2>/dev/null; then
            kill $pid
            rm "$pid_file"
            echo -e "${GREEN}✅ $service_name 已停止${NC}"
        else
            rm "$pid_file"
        fi
    fi
}

# 停止所有服务
stop_all_services() {
    clear_screen
    print_logo
    echo -e "\n${BLUE}${BOLD}🛑 停止所有服务${NC}\n"
    
    # 停止开发模式的API
    stop_service "$PID_DIR/api-dev.pid" "FastAPI Dev Server"
    
    # 停止Docker Compose
    echo "停止Docker服务栈..."
    docker compose down
    echo -e "${GREEN}✅ Docker服务栈已停止${NC}"
    
    echo -e "\n${GREEN}✅ 所有服务已停止！${NC}"
    echo -e "\n按任意键返回主菜单..."
    read -n 1
}


# 启动GUI
launch_gui() {
    echo -e "${YELLOW}启动AI监理系统GUI...${NC}"
    poetry run python ai_monitor/legacy_components/gui/main.py
}

# 启动Web UI
launch_ui() {
    echo -e "${YELLOW}启动Web控制面板...${NC}"
    poetry run python ai_monitor/legacy_components/gui/control_panel_server.py > "$LOGS_DIR/control-panel.log" 2>&1 &
    echo $! > "$PID_DIR/control-panel.pid"
    sleep 2
    # Open browser
    open "http://localhost:5005" 2>/dev/null || xdg-open "http://localhost:5005"
    echo -e "${GREEN}✅ Web控制面板已启动${NC}"
    echo -e "\n按任意键返回主菜单..."
    read -n 1
}


# Claude Code功能菜单
claude_code_menu() {
    while true; do
        clear_screen
        print_logo
        echo -e "\n${PURPLE}${BOLD}🤖 Claude Code 功能菜单${NC}\n"
        
        echo -e "${CYAN}1)${NC} 分析代码文件"
        echo -e "${CYAN}2)${NC} 测试Claude集成"
        echo -e "${CYAN}0)${NC} 返回主菜单"
        
        echo -e "\n${YELLOW}选择操作 [0-2]:${NC} "
        read -n 1 choice
        echo
        
        case $choice in
            1)
                echo -e "\n${YELLOW}文件路径:${NC} "
                read file_path
                poetry run python claude_code/claude_simulator.py analyze "$file_path"
                echo -e "\n按任意键继续..."
                read -n 1
                ;;
            2)
                poetry run python claude_code/mcp_tools/executor.py
                echo -e "\n按任意键继续..."
                read -n 1
                ;;
            0)
                break
                ;;
            *)
                echo -e "${RED}无效选择${NC}"
                sleep 1
                ;;
        esac
    done
}

# 日志查看菜单
logs_menu() {
    while true; do
        clear_screen
        print_logo
        echo -e "\n${YELLOW}${BOLD}📋 日志查看菜单${NC}\n"
        
        echo -e "${CYAN}1)${NC} 查看API服务日志 (Docker)"
        echo -e "${CYAN}2)${NC} 查看Ollama日志 (Docker)"
        echo -e "${CYAN}3)${NC} 查看Weaviate日志 (Docker)"
        echo -e "${CYAN}4)${NC} 查看开发模式API日志"
        echo -e "${CYAN}0)${NC} 返回主菜单"
        
        echo -e "\n${YELLOW}选择操作 [0-4]:${NC} "
        read -n 1 choice
        echo
        
        case $choice in
            1)
                echo -e "\n${CYAN}API服务日志 (Docker):${NC}"
                docker compose logs -f api
                ;;
            2)
                echo -e "\n${CYAN}Ollama日志 (Docker):${NC}"
                docker compose logs -f ollama
                ;;
            3)
                echo -e "\n${CYAN}Weaviate日志 (Docker):${NC}"
                docker compose logs -f weaviate
                ;;
            4)
                echo -e "\n${CYAN}开发模式API日志:${NC}"
                tail -n 50 "$LOGS_DIR/api-dev.log" 2>/dev/null || echo "日志文件不存在"
                echo -e "\n按任意键继续..."
                read -n 1
                ;;
            0)
                break
                ;;
            *)
                echo -e "${RED}无效选择${NC}"
                sleep 1
                ;;
        esac
    done
}

# 高级功能菜单
advanced_menu() {
    while true; do
        clear_screen
        print_logo
        echo -e "\n${PURPLE}${BOLD}⚙️  高级功能菜单${NC}\n"
        
        echo -e "${CYAN}1)${NC} 运行测试 (pytest)"
        echo -e "${CYAN}2)${NC} 系统诊断"
        echo -e "${CYAN}3)${NC} 安装/更新依赖 (poetry)"
        echo -e "${CYAN}4)${NC} 安装MCP Servers"
        echo -e "${CYAN}0)${NC} 返回主菜单"
        
        echo -e "\n${YELLOW}选择操作 [0-4]:${NC} "
        read -n 1 choice
        echo
        
        case $choice in
            1)
                echo -e "\n${YELLOW}运行测试...${NC}"
                poetry run pytest -q
                echo -e "\n按任意键继续..."
                read -n 1
                ;;
            2)
                echo -e "\n${YELLOW}运行系统诊断...${NC}"
                poetry run python ai_monitor/diagnose.py
                echo -e "\n按任意键继续..."
                read -n 1
                ;;
            3)
                echo -e "\n${YELLOW}安装/更新依赖...${NC}"
                poetry install
                echo -e "\n${GREEN}✅ 依赖更新完成${NC}"
                echo -e "\n按任意键继续..."
                read -n 1
                ;;
            4)
                bash scripts/install_mcp.sh
                echo -e "\n按任意键继续..."
                read -n 1
                ;;
            0)
                break
                ;;
            *)
                echo -e "${RED}无效选择${NC}"
                sleep 1
                ;;
        esac
    done
}

# 主菜单
main_menu() {
    while true; do
        clear_screen
        print_logo
        
        echo -e "\n${GREEN}${BOLD}主菜单${NC}\n"
        
        echo -e "${CYAN}1)${NC} 🚀 启动Docker服务栈 (推荐)"
        echo -e "${CYAN}2)${NC} 🛑 停止Docker服务栈"
        echo -e "${CYAN}3)${NC} 📊 查看服务状态"
        echo -e "${CYAN}4)${NC} 💻 启动API (开发模式)"
        echo -e "${CYAN}5)${NC} 🖥️  启动GUI"
        echo -e "${CYAN}6)${NC} 🌐 启动Web控制面板"
        echo -e "${CYAN}7)${NC} 🤖 Claude Code功能"
        echo -e "${CYAN}8)${NC} 📋 查看日志"
        echo -e "${CYAN}9)${NC} ⚙️  高级功能"
        echo -e "${CYAN}0)${NC} 👋 退出"
        
        echo -e "\n${YELLOW}请选择操作 [0-9]:${NC} "
        read -n 1 choice
        echo
        
        case $choice in
            1)
                start_docker_stack
                ;;
            2)
                stop_all_services
                ;;
            3)
                show_status
                ;;
            4)
                start_api_dev
                ;;
            5)
                launch_gui
                ;;
            6)
                launch_ui
                ;;
            7)
                claude_code_menu
                ;;
            8)
                logs_menu
                ;;
            9)
                advanced_menu
                ;;
            0)
                echo -e "\n${GREEN}感谢使用本地LLM项目控制中心！${NC}"
                echo -e "${YELLOW}正在安全退出...${NC}\n"
                # Clean up background jobs
                pkill -P $$
                exit 0
                ;;
            *)
                echo -e "${RED}无效的选择，请重试${NC}"
                sleep 1
                ;;
        esac
    done
}

# 检查依赖
check_dependencies() {
    local missing_deps=()
    
    command -v poetry >/dev/null 2>&1 || missing_deps+=("poetry")
    command -v docker >/dev/null 2>&1 || missing_deps+=("docker")
    command -v ollama >/dev/null 2>&1 || missing_deps+=("ollama")
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo -e "${YELLOW}⚠️  缺少以下核心依赖:${NC}"
        printf '%s\n' "${missing_deps[@]}"
        echo -e "\n${CYAN}请先安装它们再重新运行此脚本。${NC}"
        exit 1
    fi
}

# 初始化
init() {
    # 确保目录存在
    mkdir -p "$LOGS_DIR"
    mkdir -p "$PID_DIR"
    
    # 检查依赖
    check_dependencies
}

# 单命令模式
handle_command_mode() {
    case "$1" in
        start)
            echo "Starting Docker stack in non-interactive mode..."
            docker compose up -d
            ;;
        stop)
            echo "Stopping Docker stack in non-interactive mode..."
            docker compose down
            ;;
        restart)
            echo "Restarting Docker stack in non-interactive mode..."
            docker compose down && docker compose up -d
            ;;
        status)
            docker compose ps
            ;;
        logs)
            docker compose logs -f "${2:-}" # Follow logs for a specific service or all
            ;;
        launch_ui)
            echo "Launching Web UI in non-interactive mode..."
            poetry run python ai_monitor/legacy_components/gui/control_panel_server.py &
            sleep 2
            open "http://localhost:5005" 2>/dev/null || xdg-open "http://localhost:5005"
            ;;
        gui)
            echo "Launching GUI..."
            poetry run python ai_monitor/legacy_components/gui/main.py
            ;;
        help)
            echo "Usage: $0 [start|stop|restart|status|logs|launch_ui|gui]"
            ;;
        *)
            echo "Invalid command: $1. Use 'help' for usage."
            exit 1
            ;;
    esac
    exit 0
}


# 主程序入口
main() {
    cd "$PROJECT_HOME"
    init

    # 如果提供了参数，则进入单命令模式
    if [ $# -gt 0 ]; then
        handle_command_mode "$@"
    fi
    
    # 否则，进入交互式菜单
    main_menu
}

# 运行主程序
main "$@"
