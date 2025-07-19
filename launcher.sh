#!/bin/bash
# AI监理系统 - 一键启动脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 函数定义
print_banner() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════╗"
    echo "║       AI监理系统 - 快速启动器         ║"
    echo "╚═══════════════════════════════════════╝"
    echo -e "${NC}"
}

check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓ $1 已安装${NC}"
        return 0
    else
        echo -e "${RED}✗ $1 未安装${NC}"
        return 1
    fi
}

# 主程序
print_banner

echo -e "${YELLOW}1. 环境检查${NC}"
echo "------------------------"

# 检查Python
if check_command python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo "  Python版本: $PYTHON_VERSION"
else
    echo -e "${RED}请先安装Python 3${NC}"
    exit 1
fi

# 检查Ollama
if ! check_command ollama; then
    echo -e "${YELLOW}正在安装Ollama...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install ollama
    else
        curl -fsSL https://ollama.ai/install.sh | sh
    fi
fi

echo -e "\n${YELLOW}2. 选择操作${NC}"
echo "------------------------"
echo "1) 快速安装（最小版本）"
echo "2) 启动已安装的系统"
echo "3) 运行诊断工具"
echo "4) 运行测试"
echo "5) 交互式聊天"
echo "6) 退出"

read -p "请选择 (1-6): " choice

case $choice in
    1)
        echo -e "\n${GREEN}开始快速安装...${NC}"
        
        # 创建最小项目
        mkdir -p ~/ai-monitor-quick
        cd ~/ai-monitor-quick
        
        # 创建虚拟环境
        python3 -m venv venv
        source venv/bin/activate
        
        # 安装依赖
        echo "安装依赖..."
        pip install --upgrade pip
        pip install fastapi uvicorn httpx
        
        # 复制文件
        cp "$OLDPWD/app_mini.py" ./app.py 2>/dev/null || {
            echo "创建app.py..."
            curl -o app.py https://raw.githubusercontent.com/your-repo/app_mini.py
        }
        
        # 创建启动脚本
        cat > start.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
echo "启动API服务..."
echo "地址: http://localhost:8000"
echo "文档: http://localhost:8000/docs"
uvicorn app:app --reload --host 0.0.0.0 --port 8000
EOF
        chmod +x start.sh
        
        echo -e "${GREEN}✅ 安装完成！${NC}"
        echo ""
        echo "下一步："
        echo "1. 启动Ollama: ollama serve"
        echo "2. 下载模型: ollama pull llama3.2"
        echo "3. 启动API: cd ~/ai-monitor-quick && ./start.sh"
        ;;
        
    2)
        echo -e "\n${GREEN}启动系统...${NC}"
        
        # 检查Ollama
        if ! pgrep -x "ollama" > /dev/null; then
            echo "启动Ollama..."
            ollama serve &
            sleep 3
        fi
        
        # 查找项目目录
        if [ -d ~/ai-monitor-quick ]; then
            cd ~/ai-monitor-quick
        elif [ -d ~/ai-monitor-mini ]; then
            cd ~/ai-monitor-mini
        elif [ -d ~/ai-monitor-local ]; then
            cd ~/ai-monitor-local
        else
            echo -e "${RED}找不到安装目录，请先安装${NC}"
            exit 1
        fi
        
        # 启动服务
        if [ -f start.sh ]; then
            ./start.sh
        else
            source venv/bin/activate
            uvicorn app:app --reload
        fi
        ;;
        
    3)
        echo -e "\n${GREEN}运行诊断...${NC}"
        python3 diagnose.py
        ;;
        
    4)
        echo -e "\n${GREEN}运行测试...${NC}"
        python3 test_client.py
        ;;
        
    5)
        echo -e "\n${GREEN}启动交互式聊天...${NC}"
        python3 test_client.py interactive
        ;;
        
    6)
        echo "再见！"
        exit 0
        ;;
        
    *)
        echo -e "${RED}无效选择${NC}"
        exit 1
        ;;
esac
