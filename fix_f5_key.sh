#!/bin/bash
# F5录音键修复脚本

echo "🔧 F5录音键修复工具"
echo "===================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

# 1. 重启音频服务
echo -e "\n${YELLOW}1. 重启macOS音频服务...${NC}"
sudo killall coreaudiod 2>/dev/null
sleep 2
echo -e "${GREEN}✓ 音频服务已重启${NC}"

# 2. 检查并终止占用音频的Python进程
echo -e "\n${YELLOW}2. 检查Python进程...${NC}"
AUDIO_PIDS=$(ps aux | grep -i python | grep -E "(audio|speech|voice|sound)" | grep -v grep | awk '{print $2}')
if [ ! -z "$AUDIO_PIDS" ]; then
    echo "发现可能占用音频的Python进程:"
    ps aux | grep -i python | grep -E "(audio|speech|voice|sound)" | grep -v grep
    echo -e "\n${RED}是否终止这些进程? (y/n)${NC}"
    read -n 1 answer
    echo
    if [ "$answer" = "y" ]; then
        echo $AUDIO_PIDS | xargs kill -9 2>/dev/null
        echo -e "${GREEN}✓ 已终止相关进程${NC}"
    fi
else
    echo -e "${GREEN}✓ 没有发现占用音频的Python进程${NC}"
fi

# 3. 重置语音识别权限
echo -e "\n${YELLOW}3. 重置语音识别权限...${NC}"
# 这需要在系统偏好设置中手动操作
echo "请手动检查:"
echo "1) 打开 系统偏好设置 > 安全性与隐私 > 隐私 > 麦克风"
echo "2) 确保相关应用有麦克风权限"
echo "3) 打开 系统偏好设置 > 键盘 > 听写"
echo "4) 关闭听写，等待几秒，再重新打开"
echo -e "\n按任意键继续..."
read -n 1

# 4. 检查端口占用
echo -e "\n${YELLOW}4. 检查关键端口...${NC}"
PORTS=(5000 5005 8000 8080 11434)
for port in "${PORTS[@]}"; do
    if lsof -i :$port >/dev/null 2>&1; then
        echo "端口 $port 被占用:"
        lsof -i :$port | grep LISTEN | head -1
    fi
done

# 5. 停止Docker服务
echo -e "\n${YELLOW}5. 重启Docker服务...${NC}"
cd "$(dirname "$0")"
if [ -f "docker-compose.yml" ]; then
    docker compose down 2>/dev/null
    echo -e "${GREEN}✓ Docker服务已停止${NC}"
    echo "可以使用 './control_center.sh start' 重新启动服务"
else
    echo "未找到docker-compose.yml"
fi

# 6. 清理临时文件
echo -e "\n${YELLOW}6. 清理临时文件...${NC}"
rm -rf /tmp/audio* 2>/dev/null
rm -rf /tmp/speech* 2>/dev/null
echo -e "${GREEN}✓ 临时文件已清理${NC}"

# 7. 测试F5键
echo -e "\n${GREEN}=============================${NC}"
echo -e "${GREEN}修复完成！${NC}"
echo -e "${GREEN}=============================${NC}"
echo ""
echo "请测试F5键是否恢复正常:"
echo "1. 打开任意文本输入框"
echo "2. 按下F5键"
echo "3. 应该能看到听写界面"
echo ""
echo "如果仍有问题:"
echo "1. 重启Mac电脑"
echo "2. 运行诊断脚本: python diagnose_f5_issue.py"
echo "3. 检查系统日志: Console.app"
