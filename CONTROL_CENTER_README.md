# 🚀 本地LLM项目控制中心

一个统一的控制面板，用于管理AI监理系统v2.1和Claude-Code集成系统。

## 📦 包含的系统

1. **AI监理系统 v2.1**
   - Python核心服务 (端口 8000)
   - Ollama LLM引擎 (端口 11434)
   - Weaviate向量数据库 (端口 8080)
   - Go闪电API (端口 3001)
   - Rust零延迟引擎 (端口 3002)

2. **Claude-Code集成系统 (CCIS)**
   - Claude模拟器
   - MCP工具接口
   - 批量代码生成
   - 项目脚手架

## 🎯 快速开始

### 安装控制中心

```bash
cd /Users/imac/Documents/编程/项目/本地llm项目
chmod +x install_control_center.sh
./install_control_center.sh
source ~/.zshrc
```

### 启动控制中心

```bash
# 方法1: 使用全局命令（推荐）
llm-control

# 方法2: 直接运行脚本
./control_center.sh

# 方法3: 双击桌面快捷方式
# 桌面/LLM控制中心.command
```

## 📋 控制中心功能

### 主菜单
- **1) 启动所有服务** - 一键启动所有组件
- **2) 停止所有服务** - 安全关闭所有服务
- **3) 查看服务状态** - 实时监控服务运行状态
- **4) Claude Code功能** - 代码生成和项目管理
- **5) 查看日志** - 查看各服务的运行日志
- **6) 高级功能** - 测试、诊断、性能分析
- **7) 查看文档** - 阅读项目文档
- **8) 重启所有服务** - 快速重启

### Claude Code功能菜单
- 创建新项目 (Python/JavaScript/Go)
- 分析代码文件
- 编写代码
- 批量重构
- 查看输出目录

### 高级功能
- 运行完整测试套件
- 性能基准测试
- 系统诊断
- 清理输出目录
- 更新依赖

## 🛠️ 系统要求

- macOS 10.15+
- Python 3.8+
- Docker Desktop
- Homebrew
- 8GB+ RAM
- 5GB+ 可用磁盘空间

### 可选依赖
- Go 1.19+ (用于Go API)
- Rust/Cargo (用于Rust引擎)
- Ollama (用于本地LLM)

## 🏗️ 项目结构

```
/Users/imac/Documents/编程/项目/本地llm项目/
├── control_center.sh        # 主控制中心脚本
├── ai-monitor-v2/          # AI监理系统
│   ├── core/              # Python核心服务
│   ├── performance/       # Go和Rust高性能组件
│   └── logs/             # 服务日志
├── claude_simulator.py     # Claude Code模拟器
├── claude_code_mcp_tool.py # MCP工具接口
├── claude_helper.sh        # Claude命令助手
└── health_check.py        # 健康检查工具
```

## 📊 服务端口映射

| 服务 | 端口 | 描述 |
|------|------|------|
| Python核心 | 8000 | AI监理系统主API |
| Ollama | 11434 | LLM模型服务 |
| Weaviate | 8080 | 向量数据库 |
| Go API | 3001 | 高性能API |
| Rust引擎 | 3002 | 零延迟处理 |
| Redis | 6379 | 缓存服务 |

## 🔧 常用命令

```bash
# 健康检查
python3 health_check.py

# 查看日志
tail -f ai-monitor-v2/logs/core-service.log

# Claude Code使用
claude "create a Python API project"
./claude_helper.sh create my-project Python

# 快速诊断
python3 diagnose.py
```

## 🐛 故障排除

### 服务无法启动
1. 检查端口占用: `lsof -i :端口号`
2. 查看日志文件: `ai-monitor-v2/logs/`
3. 运行诊断: `python3 diagnose.py`

### 依赖缺失
```bash
# 安装Python依赖
pip install -r ai-monitor-v2/requirements.txt

# 安装系统依赖
brew install python@3.11 ollama go rust
```

### Docker问题
1. 确保Docker Desktop正在运行
2. 检查Docker权限
3. 重启Docker服务

## 📈 性能优化

1. **内存管理**
   - 关闭不需要的服务
   - 定期清理输出目录
   - 监控内存使用

2. **CPU优化**
   - 使用服务组合而非全部启动
   - 调整并发设置
   - 利用M系列芯片加速

## 🔐 安全注意事项

- 所有服务仅监听本地地址 (127.0.0.1)
- 敏感数据存储在环境变量中
- 定期更新依赖包
- 使用最小权限原则

## 📚 相关文档

- [项目概述](README.md)
- [Claude-Code集成规范](CLAUDE_CODE_INTEGRATION_PROJECT.md)
- [技术文档](CCIS_TECHNICAL_SPECIFICATION.md)
- [部署报告](DEPLOYMENT-COMPLETE-100.md)

## 🤝 贡献

欢迎提交问题和改进建议！

## 📄 许可证

MIT License

---

**快速支持**: 如有问题，运行 `llm-control` 并选择 "系统诊断" 获取详细信息。
