#!/usr/bin/env python3
"""
本地LLM项目控制面板 - Web服务器
提供Web UI和API接口来管理所有服务
"""

from flask import Flask, send_file, jsonify, request
from flask_cors import CORS
import subprocess
import psutil
import time
import os
import json
import threading
from pathlib import Path

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 项目路径
PROJECT_HOME = Path("/Users/imac/Documents/编程/项目/本地llm项目")
AI_MONITOR_HOME = PROJECT_HOME / "ai-monitor"
LOGS_DIR = AI_MONITOR_HOME / "logs"

# 服务配置
SERVICES = {
    'ai-monitor': {
        'name': 'AI监理系统',
        'services': {
            'python-core': {
                'name': 'Python核心服务',
                'port': 8000,
                'start_cmd': f'cd {AI_MONITOR_HOME}/core && python3 main.py',
                'check_port': 8000
            },
            'ollama': {
                'name': 'Ollama LLM',
                'port': 11434,
                'start_cmd': 'ollama serve',
                'check_cmd': 'pgrep -f "ollama serve"'
            },
            'weaviate': {
                'name': 'Weaviate向量库',
                'port': 8080,
                'start_cmd': 'docker start weaviate-ai-monitor || docker run -d --name weaviate-ai-monitor -p 8080:8080 semitechnologies/weaviate:1.25.0',
                'check_cmd': 'docker ps | grep weaviate-ai-monitor'
            }
        }
    },
    'performance': {
        'name': '性能加速系统',
        'services': {
            'go-api': {
                'name': 'Go闪电API',
                'port': 3001,
                'start_cmd': f'cd {AI_MONITOR_HOME}/performance/go && go run main.go',
                'check_port': 3001
            },
            'rust-engine': {
                'name': 'Rust零延迟引擎',
                'port': 3002,
                'start_cmd': f'cd {AI_MONITOR_HOME}/performance/rust && ./target/release/ai-monitor-rust',
                'check_port': 3002
            }
        }
    },
    'claude-code': {
        'name': 'Claude Code系统',
        'services': {
            'simulator': {
                'name': '代码生成器',
                'start_cmd': 'echo "Claude Code Ready"',
                'check_cmd': 'test -f ~/.local/bin/claude'
            }
        }
    },
    'voice': {
        'name': '声音系统',
        'services': {
            'tts': {
                'name': 'TTS服务',
                'port': 5001,
                'start_cmd': f'cd {PROJECT_HOME} && python3 ai-monitor-tts-service.py',
                'check_port': 5001
            }
        }
    },
    'memory': {
        'name': '记忆系统',
        'services': {
            'weaviate': {
                'name': '向量存储',
                'port': 8080,
                'start_cmd': 'docker start weaviate-ai-monitor',
                'check_port': 8080
            }
        }
    },
    'monitor': {
        'name': '监控系统',
        'services': {
            'health': {
                'name': '健康检查',
                'start_cmd': 'echo "Monitor Ready"',
                'check_cmd': 'true'
            }
        }
    }
}

# 进程管理
running_processes = {}

def check_port(port):
    """检查端口是否被占用"""
    for conn in psutil.net_connections():
        if conn.laddr.port == port and conn.status == 'LISTEN':
            return True
    return False

def check_command(cmd):
    """执行命令检查"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True)
        return result.returncode == 0
    except:
        return False

def is_service_running(service_config):
    """检查服务是否运行"""
    if 'check_port' in service_config:
        return check_port(service_config['check_port'])
    elif 'check_cmd' in service_config:
        return check_command(service_config['check_cmd'])
    return False

def start_service(service_name, service_config):
    """启动服务"""
    try:
        # 检查是否已经运行
        if is_service_running(service_config):
            return True, "服务已在运行"
        
        # 启动服务
        if 'start_cmd' in service_config:
            # 在后台运行命令
            process = subprocess.Popen(
                service_config['start_cmd'],
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            running_processes[service_name] = process
            
            # 等待服务启动
            time.sleep(3)
            
            # 检查是否成功启动
            if is_service_running(service_config):
                return True, "服务启动成功"
            else:
                return False, "服务启动失败"
        
        return True, "服务配置完成"
    except Exception as e:
        return False, str(e)

def stop_service(service_name, service_config):
    """停止服务"""
    try:
        # 如果有记录的进程，先尝试终止
        if service_name in running_processes:
            process = running_processes[service_name]
            process.terminate()
            process.wait(timeout=5)
            del running_processes[service_name]
        
        # 根据端口终止进程
        if 'check_port' in service_config:
            port = service_config['check_port']
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    for conn in proc.connections():
                        if conn.laddr.port == port:
                            proc.terminate()
                            proc.wait(timeout=5)
                except:
                    pass
        
        # 特殊处理Docker容器
        if 'weaviate' in service_name:
            subprocess.run('docker stop weaviate-ai-monitor', shell=True)
        
        return True, "服务已停止"
    except Exception as e:
        return False, str(e)

# API路由

@app.route('/')
def index():
    """返回控制面板HTML"""
    return send_file('control_panel.html')

@app.route('/api/health')
def health_check():
    """健康检查接口"""
    health_data = {
        'status': 'healthy',
        'timestamp': int(time.time()),
        'systems': {},
        'resources': {
            'cpu': psutil.cpu_percent(interval=1),
            'memory': psutil.virtual_memory().percent,
            'disk': psutil.disk_usage('/').percent,
            'uptime': int(time.time() - psutil.boot_time())
        }
    }
    
    # 检查每个系统的状态
    for system_name, system_config in SERVICES.items():
        all_running = True
        for service_name, service_config in system_config['services'].items():
            if not is_service_running(service_config):
                all_running = False
                break
        health_data['systems'][system_name] = all_running
    
    return jsonify(health_data)

@app.route('/api/system/<system_name>/start', methods=['POST'])
def start_system(system_name):
    """启动系统"""
    if system_name not in SERVICES:
        return jsonify({'error': '未知的系统'}), 404
    
    system_config = SERVICES[system_name]
    results = []
    
    for service_name, service_config in system_config['services'].items():
        success, message = start_service(f"{system_name}_{service_name}", service_config)
        results.append({
            'service': service_name,
            'success': success,
            'message': message
        })
    
    # 检查是否所有服务都启动成功
    all_success = all(r['success'] for r in results)
    
    return jsonify({
        'success': all_success,
        'results': results
    }), 200 if all_success else 500

@app.route('/api/system/<system_name>/stop', methods=['POST'])
def stop_system(system_name):
    """停止系统"""
    if system_name not in SERVICES:
        return jsonify({'error': '未知的系统'}), 404
    
    system_config = SERVICES[system_name]
    results = []
    
    for service_name, service_config in system_config['services'].items():
        success, message = stop_service(f"{system_name}_{service_name}", service_config)
        results.append({
            'service': service_name,
            'success': success,
            'message': message
        })
    
    all_success = all(r['success'] for r in results)
    
    return jsonify({
        'success': all_success,
        'results': results
    }), 200 if all_success else 500

@app.route('/api/cache/clean', methods=['POST'])
def clean_cache():
    """清理缓存"""
    try:
        # 清理输出目录
        output_dir = Path.home() / "claude-code-output"
        if output_dir.exists():
            for file in output_dir.iterdir():
                if file.is_file():
                    file.unlink()
        
        # 清理日志文件
        if LOGS_DIR.exists():
            for log_file in LOGS_DIR.glob("*.log"):
                if log_file.stat().st_size > 100 * 1024 * 1024:  # 大于100MB
                    log_file.unlink()
        
        return jsonify({'success': True, 'message': '缓存清理成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/logs')
def view_logs():
    """查看日志页面"""
    # 这里可以返回一个日志查看页面
    return jsonify({
        'message': '日志查看功能开发中',
        'logs_dir': str(LOGS_DIR)
    })

@app.route('/docs')
def view_docs():
    """查看文档"""
    docs_path = PROJECT_HOME / "README.md"
    if docs_path.exists():
        return send_file(str(docs_path))
    return "文档未找到", 404

def cleanup():
    """清理函数"""
    # 终止所有启动的进程
    for process in running_processes.values():
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            pass

if __name__ == '__main__':
    try:
        print("🚀 启动本地LLM项目控制面板服务器...")
        print("📡 访问地址: http://localhost:8888")
        print("📊 控制面板: http://localhost:8888/control_panel.html")
        print("🛑 按 Ctrl+C 停止服务器")
        
        # 注册清理函数
        import atexit
        atexit.register(cleanup)
        
        # 启动Flask服务器
        app.run(host='0.0.0.0', port=8888, debug=False)
    except KeyboardInterrupt:
        print("\n👋 正在关闭服务器...")
        cleanup()
