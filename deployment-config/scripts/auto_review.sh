#!/bin/bash
# AI监理系统自动代码审查脚本
# 在Claude CLI停止时自动运行

set -e

echo "🔍 开始自动代码审查..."

# 检查是否在git仓库中
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "⚠️  不在git仓库中，跳过代码审查"
    exit 0
fi

# 检查是否有未提交的更改
if git diff --quiet && git diff --cached --quiet; then
    echo "✅ 没有未提交的更改"
    exit 0
fi

echo "📊 分析代码更改..."

# 获取更改的文件
changed_files=$(git diff --name-only HEAD)
staged_files=$(git diff --cached --name-only)

all_files=$(echo -e "$changed_files\n$staged_files" | sort -u | grep -v '^$')

if [ -z "$all_files" ]; then
    echo "✅ 没有文件更改"
    exit 0
fi

echo "📝 更改的文件:"
echo "$all_files"

# 代码质量检查
echo "🧪 运行代码质量检查..."

# Python文件检查
python_files=$(echo "$all_files" | grep '\.py$' || true)
if [ -n "$python_files" ]; then
    echo "🐍 检查Python文件..."
    
    # 使用ruff检查（如果可用）
    if command -v ruff &> /dev/null; then
        echo "  - 运行ruff检查..."
        echo "$python_files" | xargs ruff check --output-format=github || true
    fi
    
    # 使用black检查格式（如果可用）
    if command -v black &> /dev/null; then
        echo "  - 检查代码格式..."
        echo "$python_files" | xargs black --check --diff || true
    fi
    
    # 使用mypy类型检查（如果可用）
    if command -v mypy &> /dev/null; then
        echo "  - 运行类型检查..."
        echo "$python_files" | xargs mypy --ignore-missing-imports || true
    fi
fi

# JavaScript/TypeScript文件检查
js_files=$(echo "$all_files" | grep -E '\.(js|ts|jsx|tsx)$' || true)
if [ -n "$js_files" ]; then
    echo "📜 检查JavaScript/TypeScript文件..."
    
    # 使用eslint检查（如果可用）
    if command -v eslint &> /dev/null; then
        echo "  - 运行eslint检查..."
        echo "$js_files" | xargs eslint || true
    fi
    
    # 使用prettier检查格式（如果可用）
    if command -v prettier &> /dev/null; then
        echo "  - 检查代码格式..."
        echo "$js_files" | xargs prettier --check || true
    fi
fi

# Rust文件检查
rust_files=$(echo "$all_files" | grep '\.rs$' || true)
if [ -n "$rust_files" ]; then
    echo "🦀 检查Rust文件..."
    
    # 使用cargo check
    if [ -f "Cargo.toml" ]; then
        echo "  - 运行cargo check..."
        cargo check || true
        
        echo "  - 运行cargo fmt检查..."
        cargo fmt --check || true
        
        echo "  - 运行cargo clippy..."
        cargo clippy || true
    fi
fi

# Go文件检查
go_files=$(echo "$all_files" | grep '\.go$' || true)
if [ -n "$go_files" ]; then
    echo "🐹 检查Go文件..."
    
    # 使用go fmt检查
    if command -v go &> /dev/null; then
        echo "  - 检查go fmt..."
        echo "$go_files" | xargs gofmt -l || true
        
        echo "  - 运行go vet..."
        go vet ./... || true
        
        # 使用golangci-lint（如果可用）
        if command -v golangci-lint &> /dev/null; then
            echo "  - 运行golangci-lint..."
            golangci-lint run || true
        fi
    fi
fi

# 检查大文件
echo "📏 检查大文件..."
large_files=$(echo "$all_files" | xargs ls -la 2>/dev/null | awk '$5 > 1048576 {print $9, $5}' || true)
if [ -n "$large_files" ]; then
    echo "⚠️  发现大文件 (>1MB):"
    echo "$large_files"
fi

# 检查敏感信息
echo "🔒 检查敏感信息..."
sensitive_patterns=(
    "password"
    "secret"
    "token"
    "key"
    "api.*key"
    "auth.*token"
    "Bearer [a-zA-Z0-9]+"
    "ssh-rsa"
    "-----BEGIN"
)

for pattern in "${sensitive_patterns[@]}"; do
    if echo "$all_files" | xargs grep -i "$pattern" 2>/dev/null; then
        echo "⚠️  可能包含敏感信息: $pattern"
    fi
done

# 生成代码审查报告
echo "📊 生成代码审查报告..."

report_file="code_review_$(date +%Y%m%d_%H%M%S).md"

cat > "$report_file" << EOF
# 代码审查报告

**时间**: $(date)
**分支**: $(git branch --show-current)
**提交**: $(git rev-parse --short HEAD)

## 更改的文件
\`\`\`
$all_files
\`\`\`

## 统计信息
- 更改文件数: $(echo "$all_files" | wc -l)
- Python文件: $(echo "$python_files" | wc -l)
- JavaScript/TypeScript文件: $(echo "$js_files" | wc -l)
- Rust文件: $(echo "$rust_files" | wc -l)
- Go文件: $(echo "$go_files" | wc -l)

## 建议
1. 确保所有代码都经过了适当的测试
2. 检查代码是否符合项目的编码规范
3. 确认没有硬编码的敏感信息
4. 验证性能影响是否可接受

## 下一步
- [ ] 运行完整测试套件
- [ ] 更新文档（如果需要）
- [ ] 进行代码审查
- [ ] 准备部署

EOF

echo "📝 代码审查报告已保存到: $report_file"

# 如果有Claude CLI可用，可以进行AI代码审查
if command -v claude &> /dev/null; then
    echo "🤖 进行AI代码审查..."
    
    # 获取diff内容
    diff_content=$(git diff HEAD)
    
    if [ -n "$diff_content" ]; then
        echo "正在分析代码更改..."
        
        # 使用Claude进行代码审查
        echo "$diff_content" | claude -p "请审查这些代码更改，重点关注：
1. 代码质量和最佳实践
2. 潜在的bug和问题
3. 性能影响
4. 安全问题
5. 可维护性

请提供具体的改进建议。" > ai_review_$(date +%Y%m%d_%H%M%S).md
        
        echo "🎯 AI代码审查完成，结果已保存"
    fi
fi

echo "✅ 自动代码审查完成"
echo "📊 审查报告: $report_file"
echo "💡 建议: 查看报告并根据建议进行改进"

exit 0