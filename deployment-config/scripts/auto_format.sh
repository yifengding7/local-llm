#!/bin/bash
# 自动格式化脚本
# 在Claude CLI工具执行后运行

set -e

echo "🎨 自动格式化处理..."

# 检查是否在git仓库中
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo "📂 在git仓库中，检查文件更改..."
    
    # 获取已修改但未staged的文件
    changed_files=$(git diff --name-only 2>/dev/null || echo "")
    
    if [ -n "$changed_files" ]; then
        echo "📝 发现更改的文件:"
        echo "$changed_files"
        
        # 格式化Python文件
        python_files=$(echo "$changed_files" | grep '\.py$' || true)
        if [ -n "$python_files" ] && command -v black &> /dev/null; then
            echo "🐍 格式化Python文件..."
            echo "$python_files" | xargs black --quiet 2>/dev/null || echo "⚠️  black格式化失败"
        fi
        
        # 格式化JavaScript/TypeScript文件
        js_files=$(echo "$changed_files" | grep -E '\.(js|ts|jsx|tsx)$' || true)
        if [ -n "$js_files" ] && command -v prettier &> /dev/null; then
            echo "📜 格式化JavaScript/TypeScript文件..."
            echo "$js_files" | xargs prettier --write 2>/dev/null || echo "⚠️  prettier格式化失败"
        fi
        
        # 格式化Rust文件
        rust_files=$(echo "$changed_files" | grep '\.rs$' || true)
        if [ -n "$rust_files" ] && command -v rustfmt &> /dev/null; then
            echo "🦀 格式化Rust文件..."
            echo "$rust_files" | xargs rustfmt 2>/dev/null || echo "⚠️  rustfmt格式化失败"
        fi
        
        # 格式化Go文件
        go_files=$(echo "$changed_files" | grep '\.go$' || true)
        if [ -n "$go_files" ] && command -v gofmt &> /dev/null; then
            echo "🐹 格式化Go文件..."
            echo "$go_files" | xargs gofmt -w 2>/dev/null || echo "⚠️  gofmt格式化失败"
        fi
        
        # 格式化YAML文件
        yaml_files=$(echo "$changed_files" | grep -E '\.(yaml|yml)$' || true)
        if [ -n "$yaml_files" ] && command -v yamllint &> /dev/null; then
            echo "📋 检查YAML文件格式..."
            echo "$yaml_files" | xargs yamllint 2>/dev/null || echo "⚠️  YAML格式检查失败"
        fi
        
        # 格式化Markdown文件
        md_files=$(echo "$changed_files" | grep '\.md$' || true)
        if [ -n "$md_files" ] && command -v prettier &> /dev/null; then
            echo "📄 格式化Markdown文件..."
            echo "$md_files" | xargs prettier --write 2>/dev/null || echo "⚠️  Markdown格式化失败"
        fi
        
        echo "✅ 自动格式化完成"
    else
        echo "ℹ️  没有文件更改，跳过格式化"
    fi
else
    echo "ℹ️  不在git仓库中，跳过格式化"
fi

# 检查代码质量
echo "🔍 快速代码质量检查..."

# 检查是否有常见的代码问题
if git rev-parse --git-dir > /dev/null 2>&1; then
    # 检查是否有调试代码
    if git diff --cached | grep -E "(console\.log|print\(|debug|TODO|FIXME)" > /dev/null 2>&1; then
        echo "⚠️  发现可能的调试代码或TODO标记"
    fi
    
    # 检查是否有大文件
    large_files=$(git diff --cached --name-only | xargs ls -la 2>/dev/null | awk '$5 > 1048576 {print $9}' || true)
    if [ -n "$large_files" ]; then
        echo "⚠️  发现大文件: $large_files"
    fi
fi

echo "✅ 后置处理完成"
exit 0