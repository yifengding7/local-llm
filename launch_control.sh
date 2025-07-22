#!/bin/bash
# LLM项目控制台启动器

echo "🚀 启动 LLM 项目控制台"
echo "===================="
echo ""

# 项目目录
PROJECT_DIR="/Users/imac/Documents/编程/项目/本地llm项目"
cd "$PROJECT_DIR"

# 选择要打开的控制面板
echo "请选择控制面板类型:"
echo "1) 简洁版控制台 (推荐)"
echo "2) 完整版控制面板 (需要Python服务器)"
echo "3) 命令行控制中心"
echo ""
echo -n "请输入选择 [1-3]: "
read choice

case $choice in
    1)
        echo "打开简洁版控制台..."
        # 直接在浏览器中打开HTML文件
        open "$PROJECT_DIR/control_panel_simple.html"
        echo ""
        echo "✅ 控制台已在浏览器中打开"
        echo "💡 提示: 这是一个独立的HTML界面，可以直接使用"
        ;;
        
    2)
        echo "启动完整版控制面板..."
        # 检查Python和Flask
        if ! python3 -c "import flask" 2>/dev/null; then
            echo "安装Flask..."
            pip3 install flask flask-cors
        fi
        
        # 启动服务器并打开浏览器
        chmod +x start_control_panel.sh
        ./start_control_panel.sh
        ;;
        
    3)
        echo "启动命令行控制中心..."
        chmod +x control_center.sh
        ./control_center.sh
        ;;
        
    *)
        echo "无效的选择，启动默认控制台..."
        open "$PROJECT_DIR/control_panel_simple.html"
        ;;
esac

echo ""
echo "🎉 感谢使用 LLM 项目控制台！"
