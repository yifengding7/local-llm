{
  description = "AI监理系统 v2.2 - 统一开发环境";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
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
          pydantic-settings
          python-multipart
          httpx
          aiofiles
          aiohttp
          
          # 安全认证
          python-jose
          passlib
          
          # AI/LLM相关
          numpy
          
          # 数据库客户端
          asyncpg
          aioredis
          
          # 监控和指标
          prometheus-client
          psutil
          
          # 工具库
          loguru
          python-dotenv
          click
          rich
          typer
          gitpython
          
          # 开发工具
          black
          pytest
          pytest-asyncio
          mypy
          ipython
        ]);

        # 自定义启动脚本
        startScript = pkgs.writeShellScriptBin "start-services" ''
          echo "🚀 启动AI监理系统服务..."
          
          # 启动Ollama（如果已安装）
          if command -v ollama >/dev/null; then
            echo "启动 Ollama..."
            ollama serve > logs/ollama.log 2>&1 &
            OLLAMA_PID=$!
            echo $OLLAMA_PID > .pids/ollama.pid
          fi
          
          # 启动Redis
          if command -v redis-server >/dev/null; then
            echo "启动 Redis..."
            redis-server --daemonize yes --logfile logs/redis.log
          fi
          
          # 启动Python核心服务
          if [ -f "ai-monitor/core/main.py" ]; then
            echo "启动 FastAPI 核心服务..."
            cd ai-monitor && uvicorn core.main:app --reload --host 0.0.0.0 --port 8000 > ../logs/api.log 2>&1 &
            API_PID=$!
            echo $API_PID > ../.pids/api.pid
            cd ..
          elif [ -f "ai_monitor/api/main.py" ]; then
            echo "启动 FastAPI 服务..."
            uvicorn ai_monitor.api.main:app --reload --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &
            API_PID=$!
            echo $API_PID > .pids/api.pid
          fi
          
          # 启动Go服务
          if [ -d "ai-monitor-v2/performance/go" ] && [ -f "ai-monitor-v2/performance/go/main.go" ]; then
            echo "启动 Go API..."
            cd ai-monitor-v2/performance/go && go run . > ../../../logs/go-api.log 2>&1 &
            GO_PID=$!
            echo $GO_PID > ../../../.pids/go-api.pid
            cd ../../..
          fi
          
          # 启动Rust引擎
          if [ -d "ai-monitor-v2/performance/rust" ] && [ -f "ai-monitor-v2/performance/rust/Cargo.toml" ]; then
            echo "启动 Rust 引擎..."
            cd ai-monitor-v2/performance/rust && cargo run --release > ../../../logs/rust-engine.log 2>&1 &
            RUST_PID=$!
            echo $RUST_PID > ../../../.pids/rust-engine.pid
            cd ../../..
          fi
          
          echo "✅ 所有服务已启动"
          echo "FastAPI: http://localhost:8000"
          echo "Go API: http://localhost:3001"
          echo "Rust引擎: http://localhost:3002"
          echo "Ollama: http://localhost:11434"
          
          # 等待中断信号
          trap "
            echo '🛑 停止所有服务...'
            [ -f .pids/ollama.pid ] && kill \$(cat .pids/ollama.pid) 2>/dev/null
            [ -f .pids/api.pid ] && kill \$(cat .pids/api.pid) 2>/dev/null
            [ -f .pids/go-api.pid ] && kill \$(cat .pids/go-api.pid) 2>/dev/null
            [ -f .pids/rust-engine.pid ] && kill \$(cat .pids/rust-engine.pid) 2>/dev/null
            redis-cli shutdown 2>/dev/null || true
            rm -f .pids/*.pid
            echo '✅ 所有服务已停止'
          " EXIT INT TERM
          
          wait
        '';

        # 停止服务脚本
        stopScript = pkgs.writeShellScriptBin "stop-services" ''
          echo "🛑 停止AI监理系统服务..."
          
          # 停止所有PID文件中的进程
          for pidfile in .pids/*.pid; do
            if [ -f "$pidfile" ]; then
              pid=$(cat "$pidfile")
              if kill -0 "$pid" 2>/dev/null; then
                echo "停止进程 $pid ($(basename "$pidfile" .pid))"
                kill "$pid"
              fi
              rm -f "$pidfile"
            fi
          done
          
          # 停止Redis
          redis-cli shutdown 2>/dev/null || true
          
          echo "✅ 所有服务已停止"
        '';

      in
      {
        devShells.default = pkgs.mkShell {
          name = "ai-monitor-dev";
          
          buildInputs = with pkgs; [
            # Python环境
            pythonEnv
            poetry
            python312Packages.pip
            
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
            stopScript
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
            export RUST_BACKTRACE="1"
            export RUST_LOG="debug"
            export CGO_ENABLED="1"
            
            # 创建必要的目录
            mkdir -p logs data models .cache .pids
            
            # 检查关键服务
            echo "🔍 服务检查："
            command -v ollama >/dev/null && echo "  ✅ Ollama" || echo "  ⚠️  Ollama (需手动安装)"
            command -v redis-cli >/dev/null && echo "  ✅ Redis" || echo "  ❌ Redis"
            command -v psql >/dev/null && echo "  ✅ PostgreSQL" || echo "  ❌ PostgreSQL"
            
            echo ""
            echo "🎯 快速命令："
            echo "  • start-services  - 启动所有服务"
            echo "  • stop-services   - 停止所有服务"
            echo "  • ./control_center.sh - 控制中心"
            echo "  • make setup      - 初始化项目"
            echo "  • make test       - 运行测试"
            echo ""
            echo "💡 提示: 使用 'direnv allow' 自动加载环境"
            echo ""
          '';
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
          buildInputs = with pkgs; [ rustc cargo rustfmt rust-analyzer pkg-config ];
        };
      });
}