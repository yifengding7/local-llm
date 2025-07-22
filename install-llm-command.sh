#!/usr/bin/env bash
# LLM命令安装脚本

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m'

PROJECT_DIR="/Users/imac/Documents/编程/项目/本地llm项目"
LLM_CMD="$PROJECT_DIR/llm"

echo -e "${BLUE}🚀 安装 LLM 命令...${NC}"

# 1. 创建软链接到/usr/local/bin（适用于非Nix环境）
if [ -w "/usr/local/bin" ]; then
    echo "创建全局命令链接..."
    sudo ln -sf "$LLM_CMD" /usr/local/bin/llm
    echo -e "${GREEN}✅ 已创建全局命令 'llm'${NC}"
fi

# 2. 添加到用户PATH（备选方案）
SHELL_RC=""
case "$SHELL" in
    */bash)
        SHELL_RC="$HOME/.bashrc"
        ;;
    */zsh)
        SHELL_RC="$HOME/.zshrc"
        ;;
    */fish)
        SHELL_RC="$HOME/.config/fish/config.fish"
        ;;
esac

if [ -n "$SHELL_RC" ]; then
    # 检查是否已添加
    if ! grep -q "# LLM Command" "$SHELL_RC" 2>/dev/null; then
        echo -e "\n# LLM Command" >> "$SHELL_RC"
        echo "export PATH=\"$PROJECT_DIR:\$PATH\"" >> "$SHELL_RC"
        echo -e "${GREEN}✅ 已添加到 $SHELL_RC${NC}"
        echo -e "${YELLOW}请运行 'source $SHELL_RC' 或重新打开终端${NC}"
    fi
fi

# 3. 测试命令
echo -e "\n${BLUE}测试命令...${NC}"
if command -v llm &> /dev/null; then
    echo -e "${GREEN}✅ 命令安装成功！${NC}"
    echo ""
    echo "可用命令："
    echo "  llm         - 启动Web控制面板"
    echo "  llm start   - 启动所有服务"
    echo "  llm status  - 查看服务状态"
    echo "  llm help    - 查看所有命令"
else
    echo -e "${YELLOW}⚠️  命令尚未生效，请：${NC}"
    echo "1. 运行: source $SHELL_RC"
    echo "2. 或重新打开终端"
fi

echo ""
echo -e "${GREEN}🎉 安装完成！${NC}"
