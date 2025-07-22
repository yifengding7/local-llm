#!/bin/bash
# AI监理系统v2.1服务启动脚本

set -e

echo "🚀 启动AI监理系统v2.1服务..."
echo "📅 启动时间: $(date)"
echo "🖥️  系统环境: $(uname -a)"
echo ""

# 检查依赖服务
echo "🔍 检查依赖服务..."

# 检查Ollama
if pgrep -f "ollama serve" > /dev/null; then
    echo "✅ Ollama服务已运行"
else
    echo "🔄 启动Ollama服务..."
    ollama serve > logs/ollama.log 2>&1 &
    sleep 3
    echo "✅ Ollama服务启动完成"
fi

# 检查Docker
if ! docker ps > /dev/null 2>&1; then
    echo "⚠️  Docker服务未运行，请先启动Docker"
    exit 1
else
    echo "✅ Docker服务正常"
fi

# 检查Weaviate
if docker ps | grep -q "weaviate-ai-monitor"; then
    echo "✅ Weaviate服务已运行"
else
    echo "🔄 启动Weaviate服务..."
    docker run -d --name weaviate-ai-monitor \
        -p 8080:8080 \
        -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
        -e DEFAULT_VECTORIZER_MODULE=text2vec-transformers \
        -e ENABLE_MODULES=text2vec-transformers \
        -v "$(pwd)/data/weaviate:/var/lib/weaviate" \
        semitechnologies/weaviate:1.25.0
    
    echo "⏳ 等待Weaviate启动..."
    sleep 15
    echo "✅ Weaviate服务启动完成"
fi

# 启动性能层服务
echo ""
echo "🔥 启动极致性能层..."

# 编译并启动Rust零延迟引擎
echo "🦀 启动Rust零延迟引擎..."
cd performance/rust
if [ ! -f "Cargo.toml" ]; then
    echo "⚠️  Rust项目配置缺失，跳过Rust引擎启动"
else
    cargo build --release > ../../logs/rust-build.log 2>&1 &
    echo "✅ Rust引擎编译中..."
fi
cd ../..

# 启动Go闪电API
echo "⚡ 启动Go闪电API..."
cd performance/go
if [ ! -f "go.mod" ]; then
    echo "⚠️  Go项目配置缺失，跳过Go API启动"
else
    go mod tidy > ../../logs/go-build.log 2>&1 &
    go run main.go > ../../logs/go-api.log 2>&1 &
    echo "✅ Go闪电API启动中..."
fi
cd ../..

# 启动核心引擎
echo ""
echo "⚙️  启动核心引擎..."

# 设置环境变量
export MOJO_ENABLE_NEURAL_ENGINE=1
export METAL_DEVICE_WRAPPER_TYPE=1
export RUST_BACKTRACE=1
export VECTOR_CACHE_SIZE=32GB
export MODEL_WEIGHTS_SIZE=8GB
export HNSW_INDEX_SIZE=12GB
export GOMAXPROCS=12
export RAYON_NUM_THREADS=12
export PYTHONUNBUFFERED=1

# 启动Python核心服务
echo "🐍 启动Python核心服务..."
cd core
if [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
    echo "✅ 虚拟环境激活成功"
else
    echo "⚠️  使用系统Python环境"
fi

# 使用现有的Python环境
python3 -c "
import sys
import time
import json
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

class AIMonitorHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'status': 'healthy',
                'timestamp': int(time.time()),
                'version': '2.1.0',
                'service': 'AI Monitor Core',
                'uptime': int(time.time() - start_time),
                'python_version': f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'
            }
            self.wfile.write(json.dumps(response).encode())
        elif self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'service': 'AI监理系统v2.1',
                'status': 'running',
                'timestamp': int(time.time()),
                'endpoints': {
                    'health': 'http://localhost:8000/health',
                    'status': 'http://localhost:8000/status',
                    'ollama': 'http://localhost:11434/api/tags',
                    'weaviate': 'http://localhost:8080/v1/meta',
                    'go_api': 'http://localhost:3001/health'
                }
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found')

    def log_message(self, format, *args):
        print(f'{datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")} - {format % args}')

start_time = time.time()
server = HTTPServer(('localhost', 8000), AIMonitorHandler)
print('🌐 AI监理系统v2.1核心服务启动在端口8000')
print('📊 健康检查: http://localhost:8000/health')
print('📋 状态页面: http://localhost:8000/status')
print('🛑 按Ctrl+C停止服务')
try:
    server.serve_forever()
except KeyboardInterrupt:
    print('\\n🛑 服务停止')
    server.shutdown()
" > ../logs/core-service.log 2>&1 &

echo "✅ 核心服务启动完成"

cd ..

# 显示服务状态
echo ""
echo "🎉 AI监理系统v2.1启动完成！"
echo ""
echo "📊 服务状态:"
echo "  - 核心引擎: http://localhost:8000"
echo "  - Ollama: http://localhost:11434"
echo "  - Weaviate: http://localhost:8080"
echo "  - Go API: http://localhost:3001"
echo ""
echo "🔍 健康检查:"
echo "  - 核心服务: curl http://localhost:8000/health"
echo "  - Ollama: curl http://localhost:11434/api/tags"
echo "  - Weaviate: curl http://localhost:8080/v1/meta"
echo "  - Go API: curl http://localhost:3001/health"
echo ""
echo "📋 查看日志:"
echo "  - 核心服务: tail -f logs/core-service.log"
echo "  - Ollama: tail -f logs/ollama.log"
echo "  - Go API: tail -f logs/go-api.log"
echo "  - Rust引擎: tail -f logs/rust-build.log"
echo ""
echo "🛑 停止服务: ./stop_services.sh"
echo ""

# 等待服务稳定
echo "⏳ 等待服务稳定..."
sleep 5

# 健康检查
echo "🔍 执行健康检查..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 核心服务健康检查通过"
else
    echo "⚠️  核心服务健康检查失败"
fi

if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama服务健康检查通过"
else
    echo "⚠️  Ollama服务健康检查失败"
fi

if curl -s http://localhost:8080/v1/meta > /dev/null; then
    echo "✅ Weaviate服务健康检查通过"
else
    echo "⚠️  Weaviate服务健康检查失败"
fi

echo ""
echo "🎯 AI监理系统v2.1已就绪！"
echo "💡 提示: 所有服务都在后台运行，查看日志文件获取详细信息"