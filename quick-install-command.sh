#!/bin/bash
# 一键安装命令生成器

cat > install_ai_monitor.sh << 'EOF'
#!/bin/bash
# AI监理系统 - 快速安装器

echo "🚀 开始安装AI监理系统 v2.1..."

# 下载安装脚本
curl -fsSL https://raw.githubusercontent.com/your-repo/ai-monitor-v2/main/install_mac.sh -o /tmp/install_mac.sh

# 或者使用本地脚本
# cp install_mac.sh /tmp/install_mac.sh

# 赋予执行权限
chmod +x /tmp/install_mac.sh

# 执行安装
/tmp/install_mac.sh

# 清理
rm -f /tmp/install_mac.sh
EOF

echo "==================================="
echo "🎯 一键安装命令："
echo ""
echo "curl -fsSL https://your-domain.com/install.sh | bash"
echo ""
echo "或使用本地文件："
echo ""
echo "bash install_mac.sh"
echo "==================================="
