#!/bin/bash
# F5录音键问题最终修复方案

echo "🔧 F5录音键问题 - 根本原因修复"
echo "================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "\n${YELLOW}问题诊断：${NC}"
echo "本地LLM项目中的音频/语音相关服务可能与macOS系统的语音识别服务冲突"
echo "特别是TTS（文本转语音）服务和控制面板服务"

# 1. 停止所有项目服务
echo -e "\n${BLUE}步骤1: 停止所有项目服务${NC}"
cd "$(dirname "$0")"

# 停止控制中心
if [ -f "control_center.sh" ]; then
    echo "停止control_center服务..."
    ./control_center.sh stop 2>/dev/null || true
fi

# 停止Docker服务
echo "停止Docker服务..."
docker compose down 2>/dev/null || true

# 终止所有Python进程（属于本项目的）
echo "终止项目相关的Python进程..."
pkill -f "python.*ai-monitor" 2>/dev/null || true
pkill -f "python.*llm.*项目" 2>/dev/null || true
pkill -f "python.*control_panel" 2>/dev/null || true
pkill -f "python.*tts" 2>/dev/null || true

# 2. 清理端口占用
echo -e "\n${BLUE}步骤2: 清理端口占用${NC}"
PORTS=(5000 5001 5005 8000 8080 8888 11434 3001 3002)
for port in "${PORTS[@]}"; do
    PID=$(lsof -ti :$port 2>/dev/null)
    if [ ! -z "$PID" ]; then
        echo "清理端口 $port (PID: $PID)..."
        kill -9 $PID 2>/dev/null || true
    fi
done

# 3. 重启音频服务
echo -e "\n${BLUE}步骤3: 重启macOS音频服务${NC}"
sudo killall coreaudiod 2>/dev/null || true
sleep 3
echo -e "${GREEN}✓ 音频服务已重启${NC}"

# 4. 清理系统缓存
echo -e "\n${BLUE}步骤4: 清理系统缓存${NC}"
rm -rf /tmp/audio* 2>/dev/null
rm -rf /tmp/speech* 2>/dev/null
rm -rf ~/Library/Caches/com.apple.speech* 2>/dev/null || true
echo -e "${GREEN}✓ 缓存已清理${NC}"

# 5. 检查并修复权限
echo -e "\n${BLUE}步骤5: 检查系统权限${NC}"
echo "请手动检查以下设置："
echo "1. 系统偏好设置 → 安全性与隐私 → 隐私 → 麦克风"
echo "   - 确保终端/Terminal有权限"
echo "2. 系统偏好设置 → 键盘 → 听写"
echo "   - 关闭听写"
echo "   - 等待5秒"
echo "   - 重新开启听写"
echo "   - 确认快捷键设置为F5"
echo -e "\n${YELLOW}按任意键继续...${NC}"
read -n 1

# 6. 测试F5键
echo -e "\n${BLUE}步骤6: 测试F5键${NC}"
echo "请现在测试F5键："
echo "1. 打开文本编辑器或任意输入框"
echo "2. 按下F5键"
echo "3. 应该看到听写界面"
echo -e "\n${YELLOW}F5键是否正常工作？(y/n)${NC}"
read -n 1 answer
echo

if [ "$answer" = "y" ]; then
    echo -e "\n${GREEN}太好了！问题已解决。${NC}"
    echo -e "\n${YELLOW}建议的使用方式：${NC}"
    echo "1. 使用项目时，避免启动TTS（文本转语音）相关服务"
    echo "2. 如果需要同时使用项目和语音输入："
    echo "   - 先使用语音输入"
    echo "   - 再启动项目服务"
    echo "   - 或使用其他语音输入方法（如手机+通用剪贴板）"
else
    echo -e "\n${RED}问题仍然存在。${NC}"
    echo -e "\n${YELLOW}请尝试以下高级修复：${NC}"
    echo "1. 重启Mac电脑"
    echo "2. 在安全模式下测试"
    echo "3. 创建新用户账户测试"
    echo "4. 检查Console.app中的系统日志"
    echo "5. 重置NVRAM/PRAM（开机时按住Option+Command+P+R）"
fi

# 7. 创建安全启动脚本
echo -e "\n${BLUE}创建安全启动脚本...${NC}"
cat > start_safe.sh << 'EOF'
#!/bin/bash
# 安全启动脚本 - 避免音频冲突

echo "🚀 安全启动本地LLM项目（避免音频冲突）"

# 只启动核心服务，不启动音频相关服务
docker compose up -d api ollama weaviate

echo "✅ 核心服务已启动"
echo "⚠️  未启动音频/TTS相关服务以避免F5键冲突"
EOF

chmod +x start_safe.sh
echo -e "${GREEN}✓ 安全启动脚本已创建: ./start_safe.sh${NC}"

# 8. 更新项目配置建议
echo -e "\n${BLUE}项目配置优化建议：${NC}"
cat > F5_FIX_RECOMMENDATIONS.md << 'EOF'
# F5键兼容性修复建议

## 问题根源
- TTS（文本转语音）服务可能占用音频输入通道
- 控制面板服务可能与系统服务冲突
- Python进程可能锁定音频设备

## 代码修改建议

### 1. 修改control_panel_server.py
移除或注释掉TTS服务配置：
```python
# 'voice': {
#     'name': '声音系统',
#     'services': {
#         'tts': {
#             'name': 'TTS服务',
#             'port': 5001,
#             'start_cmd': f'cd {PROJECT_HOME} && python3 ai-monitor-tts-service.py',
#             'check_port': 5001
#         }
#     }
# },
```

### 2. 修改端口配置
避免使用5000-5010端口范围（系统音频服务常用）

### 3. 添加音频检查
在启动服务前检查音频服务状态

## 使用建议
1. 使用 `./start_safe.sh` 代替 `./control_center.sh start`
2. 如需TTS功能，考虑使用Web API而非本地服务
3. 定期检查系统日志确保无冲突
EOF

echo -e "\n${GREEN}=============================${NC}"
echo -e "${GREEN}修复脚本执行完成！${NC}"
echo -e "${GREEN}=============================${NC}"
echo ""
echo "总结："
echo "- 已停止所有可能冲突的服务"
echo "- 已重启音频服务"
echo "- 已创建安全启动脚本"
echo "- 已生成修复建议文档"
echo ""
echo "如果问题解决，使用 ./start_safe.sh 启动项目"
echo "如果问题持续，请查看 F5_FIX_RECOMMENDATIONS.md"
