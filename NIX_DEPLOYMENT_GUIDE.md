# 🚀 AI监理系统 Nix 环境自动化部署指南

> **任务目标**: 将本项目从混合环境管理迁移到统一的Nix声明式环境管理
> **执行者**: Kiro (AI助手)
> **预计时间**: 30分钟

## 📋 前置检查

在开始之前，请验证以下条件：
- 当前目录: `/Users/imac/Documents/编程/项目/本地llm项目`
- 系统: macOS (Apple Silicon M3)
- 网络: 可访问 github.com 和 nixos.org

## 🎯 Step 1: 安装和配置Nix

### 1.1 检查Nix是否已安装
```bash
if command -v nix >/dev/null 2>&1; then
    echo "✅ Nix 已安装，版本: $(nix --version)"
else
    echo "❌ Nix 未安装，开始安装..."
    # 安装Nix (多用户模式)
    sh <(curl -L https://nixos.org/nix/install) --daemon
    
    # 重新加载shell配置
    source /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
fi
```

### 1.2 启用Flakes特性
```bash
# 创建配置目录
mkdir -p ~/.config/nix

# 添加实验性特性配置
cat >> ~/.config/nix/nix.conf << 'EOF'
experimental-features = nix-command flakes
max-jobs = auto
cores = 0
sandbox = false
extra-substituters = https://cache.nixos.org https://nix-community.cachix.org
extra-trusted-public-keys = cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY= nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs=
EOF

echo "✅ Nix Flakes 已启用"
```

## 🎯 Step 2: 分析项目依赖

### 2.1 扫描Python依赖
```bash
# 收集所有Python依赖
echo "📊 分析Python依赖..."
find . -name "requirements*.txt" -o -name "pyproject.toml" | while read file; do
    echo "Found: $file"
    cat "$file"
done > /tmp/python_deps_analysis.txt
```

### 2.2 扫描其他语言依赖
```bash
# Go依赖
if [ -f "go.mod" ]; then
    echo "📊 发现Go项目"
    grep -E "^require" go.mod
fi

# Rust依赖
if [ -f "Cargo.toml" ]; then
    echo "📊 发现Rust项目"
    grep -A 20 "[dependencies]" Cargo.toml
fi

# Node.js依赖
if [ -f "package.json" ]; then
    echo "📊 发现Node.js项目"
    jq '.dependencies, .devDependencies' package.json
fi
```

## 🎯 Step 3: 创建Nix配置文件

### 3.1 创建主配置文件 flake.nix
```bash
cat > flake.nix << 'EOF'
{
  description = "AI监理系统 v2.2 - 统一开发环境";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config = {
            allowUnfree = true;
            permittedInsecurePackages = [];
          };
        };

        # Python环境配置
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          # Web框架
          fastapi
          uvicorn
          pydantic
          python-multipart
          httpx
          aiofiles
          
          # AI/LLM
          openai
          anthropic
          
          # 数据处理
          numpy
          pandas
          
          # 向量数据库
          chromadb
          
          # 工具库
          loguru
          python-dotenv
          click
          rich
          typer
          
          # 开发工具
          black
          ruff
          pytest
          ipython
          
          # Git操作
          gitpython
        ]);

        # 自定义启动脚本
        startScript = pkgs.writeShellScriptBin "start-services" ''
          echo "🚀 启动AI监理系统服务..."
          
          # 启动Ollama（如果已安装）
          if command -v ollama >/dev/null; then
            echo "启动 Ollama..."
            ollama serve &
            OLLAMA_PID=$!
          fi
          
          # 启动Redis
          if command -v redis-server >/dev/null; then
            echo "启动 Redis..."
            redis-server --daemonize yes
          fi
          
          # 启动Python API
          if [ -f "main.py" ]; then
            echo "启动 FastAPI..."
            uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
            API_PID=$!
          fi
          
          # 启动Go服务
          if [ -d "go-api" ] && [ -f "go-api/main.go" ]; then
            echo "启动 Go API..."
            cd go-api && go run . &
            GO_PID=$!
            cd ..
          fi
          
          echo "✅ 所有服务已启动"
          echo "FastAPI: http://localhost:8000"
          echo "Go API: http://localhost:3001"
          
          # 等待中断信号
          trap "kill $OLLAMA_PID $API_PID $GO_PID 2>/dev/null; redis-cli shutdown" EXIT
          wait
        '';

      in
      {
        devShells.default = pkgs.mkShell {
          name = "ai-monitor-dev";
          
          buildInputs = with pkgs; [
            # Python环境
            pythonEnv
            poetry
            pip
            
            # Go环境
            go_1_22
            gopls
            golangci-lint
            
            # Rust环境
            rustc
            cargo
            rustfmt
            rust-analyzer
            pkg-config
            
            # Node.js环境
            nodejs_20
            nodePackages.pnpm
            nodePackages.npm
            
            # 数据库和服务
            redis
            postgresql_15
            sqlite
            
            # 系统工具
            git
            gnumake
            jq
            yq-go
            tree
            htop
            curl
            wget
            
            # 开发工具
            neovim
            tmux
            direnv
            
            # 自定义脚本
            startScript
          ];
          
          shellHook = ''
            echo ""
            echo "╔════════════════════════════════════════╗"
            echo "║     🤖 AI监理系统 v2.2 开发环境       ║"
            echo "╚════════════════════════════════════════╝"
            echo ""
            echo "📦 环境信息："
            echo "  • Python ${pythonEnv.version}"
            echo "  • Go ${pkgs.go_1_22.version}"
            echo "  • Rust ${pkgs.rustc.version}"
            echo "  • Node.js ${pkgs.nodejs_20.version}"
            echo ""
            
            # 设置环境变量
            export PROJECT_ROOT="$PWD"
            export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
            export AI_MONITOR_ENV="development"
            
            # 创建必要的目录
            mkdir -p logs data models .cache
            
            # 检查关键服务
            echo "🔍 服务检查："
            command -v ollama >/dev/null && echo "  ✅ Ollama" || echo "  ⚠️  Ollama (需手动安装)"
            command -v redis-cli >/dev/null && echo "  ✅ Redis" || echo "  ❌ Redis"
            command -v psql >/dev/null && echo "  ✅ PostgreSQL" || echo "  ❌ PostgreSQL"
            
            echo ""
            echo "🎯 快速命令："
            echo "  • start-services  - 启动所有服务"
            echo "  • make setup      - 初始化项目"
            echo "  • make test       - 运行测试"
            echo "  • python main.py  - 启动主程序"
            echo ""
            echo "💡 提示: 使用 'direnv allow' 自动加载环境"
            echo ""
          '';
          
          # 环境变量
          RUST_BACKTRACE = "1";
          RUST_LOG = "debug";
          CGO_ENABLED = "1";
        };
        
        # 额外的专用shell
        devShells.python = pkgs.mkShell {
          name = "ai-monitor-python";
          buildInputs = [ pythonEnv pkgs.poetry ];
        };
        
        devShells.go = pkgs.mkShell {
          name = "ai-monitor-go";
          buildInputs = with pkgs; [ go_1_22 gopls golangci-lint ];
        };
        
        devShells.rust = pkgs.mkShell {
          name = "ai-monitor-rust";
          buildInputs = with pkgs; [ rustc cargo rustfmt rust-analyzer ];
        };
      });
}
EOF

echo "✅ flake.nix 已创建"
```

### 3.2 创建向后兼容的 shell.nix
```bash
cat > shell.nix << 'EOF'
# 为不使用flakes的用户提供兼容性
(builtins.getFlake (toString ./.)).devShells.${builtins.currentSystem}.default
EOF

echo "✅ shell.nix 已创建"
```

### 3.3 创建 .envrc (支持direnv自动加载)
```bash
cat > .envrc << 'EOF'
use flake
layout python

# 项目特定的环境变量
export AI_MONITOR_VERSION="2.2"
export LOG_LEVEL="INFO"
dotenv_if_exists .env.local
EOF

echo "✅ .envrc 已创建"
```

## 🎯 Step 4: 构建和验证环境

### 4.1 首次构建环境
```bash
echo "🔨 开始构建Nix环境（首次构建需要下载依赖，请耐心等待）..."
nix develop --build -c echo "✅ 环境构建成功！"
```

### 4.2 验证各语言环境
```bash
# 在Nix环境中验证
nix develop -c bash << 'EOF'
echo "🧪 验证环境组件..."

# Python验证
echo -n "Python: "
python --version
python -c "import fastapi, pydantic; print('✅ 核心包已安装')"

# Go验证
echo -n "Go: "
go version

# Rust验证  
echo -n "Rust: "
rustc --version

# Node.js验证
echo -n "Node.js: "
node --version

# 工具验证
echo "工具链:"
for tool in git make redis-cli psql; do
    if command -v $tool >/dev/null; then
        echo "  ✅ $tool"
    else
        echo "  ❌ $tool"
    fi
done
EOF
```

## 🎯 Step 5: 迁移现有依赖

### 5.1 分析并迁移Python依赖
```bash
# 如果存在requirements.txt，创建迁移脚本
if [ -f "requirements.txt" ]; then
    cat > migrate_python_deps.py << 'EOF'
#!/usr/bin/env python3
import re

# 读取requirements.txt
with open('requirements.txt', 'r') as f:
    deps = f.readlines()

# 转换为Nix格式
nix_deps = []
for dep in deps:
    dep = dep.strip()
    if dep and not dep.startswith('#'):
        # 提取包名（忽略版本号）
        pkg_name = re.split('[<>=!]', dep)[0]
        # 转换为Nix Python包名格式
        nix_name = pkg_name.replace('-', '_').replace('.', '_')
        nix_deps.append(f"ps.{nix_name}")

print("# Python依赖列表（添加到flake.nix中）:")
for dep in sorted(set(nix_deps)):
    print(f"  {dep}")
EOF

    python migrate_python_deps.py
fi
```

### 5.2 创建统一启动脚本
```bash
cat > nix-start.sh << 'EOF'
#!/usr/bin/env bash
set -e

echo "🚀 使用Nix环境启动AI监理系统..."

# 确保在项目根目录
cd "$(dirname "$0")"

# 进入Nix环境并启动服务
exec nix develop -c start-services
EOF

chmod +x nix-start.sh
echo "✅ 启动脚本已创建: ./nix-start.sh"
```

## 🎯 Step 6: 集成到现有工作流

### 6.1 更新Makefile（如果存在）
```bash
if [ -f "Makefile" ]; then
    # 备份原Makefile
    cp Makefile Makefile.backup
    
    # 添加Nix相关目标
    cat >> Makefile << 'EOF'

# Nix环境目标
.PHONY: nix-shell nix-build nix-clean

nix-shell:
	@echo "进入Nix开发环境..."
	nix develop

nix-build:
	@echo "构建Nix环境..."
	nix develop --build

nix-clean:
	@echo "清理Nix缓存..."
	nix-collect-garbage -d

nix-start:
	@echo "在Nix环境中启动服务..."
	./nix-start.sh
EOF
    
    echo "✅ Makefile 已更新"
fi
```

### 6.2 创建环境切换脚本
```bash
cat > switch-to-nix.sh << 'EOF'
#!/usr/bin/env bash

echo "🔄 切换到Nix环境管理..."

# 停用Python虚拟环境
if [ -n "$VIRTUAL_ENV" ]; then
    echo "停用当前虚拟环境: $VIRTUAL_ENV"
    deactivate 2>/dev/null || true
fi

# 进入Nix shell
echo "进入Nix开发环境..."
exec nix develop
EOF

chmod +x switch-to-nix.sh
```

## 🎯 Step 7: 验证部署成功

### 7.1 运行集成测试
```bash
cat > test_nix_env.sh << 'EOF'
#!/usr/bin/env bash

echo "🧪 运行Nix环境集成测试..."

# 测试Python导入
nix develop -c python -c "
import fastapi
import uvicorn
import pydantic
print('✅ Python核心依赖正常')
"

# 测试命令可用性
COMMANDS="python go rustc node git make redis-cli"
for cmd in $COMMANDS; do
    if nix develop -c which $cmd >/dev/null 2>&1; then
        echo "✅ $cmd 可用"
    else
        echo "❌ $cmd 不可用"
    fi
done

# 测试服务启动（5秒后自动退出）
echo "测试服务启动..."
timeout 5 nix develop -c start-services || true
echo "✅ 服务启动测试完成"
EOF

chmod +x test_nix_env.sh
./test_nix_env.sh
```

## 📝 后续步骤

1. **更新项目文档**
   - 在README.md中添加Nix环境使用说明
   - 更新开发者指南

2. **配置CI/CD**
   - 在GitHub Actions中使用Nix
   - 确保构建的一致性

3. **团队培训**
   - 分享Nix基本命令
   - 创建常见问题解答

## 🆘 故障排除

### 问题1: Nix命令未找到
```bash
# 重新加载shell配置
source /etc/profile
# 或重新打开终端
```

### 问题2: 构建失败
```bash
# 清理缓存重试
nix-collect-garbage -d
nix develop --rebuild
```

### 问题3: Python包未找到
```bash
# 搜索正确的包名
nix search nixpkgs python312Packages.包名
```

## ✅ 部署完成检查清单

- [ ] Nix已安装并配置
- [ ] flake.nix文件已创建
- [ ] 环境构建成功
- [ ] Python依赖可用
- [ ] Go环境正常
- [ ] Rust环境正常
- [ ] 启动脚本工作正常
- [ ] 服务可以启动

---

**执行完成后，请运行以下命令验证:**
```bash
cd /Users/imac/Documents/编程/项目/本地llm项目
nix develop -c echo "🎉 Nix环境部署成功！"
```
