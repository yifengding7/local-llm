#!/bin/bash
# 创建桌面快捷方式

echo "🎯 创建 LLM 控制台桌面快捷方式"
echo "=============================="
echo ""

# 创建.app应用程序包
APP_NAME="LLM控制台"
APP_DIR="$HOME/Desktop/$APP_NAME.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"

# 创建目录结构
mkdir -p "$MACOS_DIR"
mkdir -p "$RESOURCES_DIR"

# 创建执行脚本
cat > "$MACOS_DIR/launcher" << 'EOF'
#!/bin/bash
# 打开 LLM 控制台
open "/Users/imac/Documents/编程/项目/本地llm项目/control_panel_simple.html"
EOF

chmod +x "$MACOS_DIR/launcher"

# 创建Info.plist
cat > "$CONTENTS_DIR/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIdentifier</key>
    <string>com.llm.control</string>
    <key>CFBundleName</key>
    <string>LLM控制台</string>
    <key>CFBundleDisplayName</key>
    <string>LLM控制台</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>CFBundleIconFile</key>
    <string>icon</string>
</dict>
</plist>
EOF

# 创建图标（使用emoji作为图标）
cat > "$RESOURCES_DIR/icon.txt" << 'EOF'
🚀
EOF

echo "✅ 桌面快捷方式创建成功！"
echo ""
echo "📍 位置: $APP_DIR"
echo "💡 使用: 双击桌面上的'LLM控制台'图标"
echo ""

# 创建Dock快捷方式脚本
cat > "$HOME/Desktop/添加到Dock.command" << 'EOF'
#!/bin/bash
# 添加到Dock
osascript -e 'tell application "Dock" to make new dock item with properties {tile type:application, tile data:file "~/Desktop/LLM控制台.app"}'
echo "✅ 已添加到Dock"
EOF

chmod +x "$HOME/Desktop/添加到Dock.command"

echo "🎉 额外创建了'添加到Dock.command'，双击可将应用添加到Dock栏"
