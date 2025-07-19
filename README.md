# AI监理系统 - 本地部署指南

## 🚨 重要说明

原始的安装脚本中很多包版本已经过时。这里提供修复后的安装方案。

## 🛠️ 快速开始（推荐）

### 1. 运行诊断工具

首先检查你的系统环境：

```bash
python3 diagnose.py
```

这会告诉你缺少什么以及如何修复。

### 2. 最简安装（5分钟）

如果你只想快速体验：

```bash
chmod +x quick_install.sh
./quick_install.sh
```

这会创建一个最小化的API服务在 `~/ai-monitor-mini`

### 3. 完整安装（修复版）

如果需要完整功能：

```bash
chmod +x install_fixed.sh
./install_fixed.sh
```

## 📋 手动安装步骤

### 前置要求

1. **安装Homebrew**（如果没有）:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **安装必要工具**:
   ```bash
   brew install python@3.11 ollama git
   ```

3. **安装Docker**（可选）:
   ```bash
   brew install --cask docker
   open /Applications/Docker.app
   ```

### 基础安装

1. **创建项目目录**:
   ```bash
   mkdir -p ~/ai-monitor-local
   cd ~/ai-monitor-local
   ```

2. **创建虚拟环境**:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   ```

3. **安装Python包**（一个一个安装以避免冲突）:
   ```bash
   pip install --upgrade pip
   pip install fastapi==0.111.0
   pip install uvicorn[standard]==0.30.1
   pip install httpx==0.27.0
   pip install pydantic==2.7.4
   pip install ollama==0.3.0
   pip install python-dotenv==1.0.1
   ```

4. **设置Ollama**:
   ```bash
   # 启动Ollama服务
   ollama serve
   
   # 在新终端中下载模型
   ollama pull llama3.2            # 3.2B参数，较快
   ollama pull qwen2.5-coder:1.5b  # 代码模型，1.5B
   ollama pull phi3:mini           # 微软小模型，3.8B
   ```

### 运行测试

1. **创建测试文件** `test_api.py`:
   ```python
   import httpx
   import asyncio
   
   async def test():
       async with httpx.AsyncClient() as client:
           # 测试Ollama
           response = await client.get("http://localhost:11434/api/tags")
           print("Ollama模型:", response.json())
   
   asyncio.run(test())
   ```

2. **运行测试**:
   ```bash
   python test_api.py
   ```

## 🐛 常见问题

### 1. "包版本冲突"

**问题**: `pip install` 报告版本冲突

**解决**:
```bash
# 使用 --force-reinstall
pip install --force-reinstall package_name==version

# 或者创建新的虚拟环境
rm -rf venv
python3 -m venv venv
source venv/bin/activate
```

### 2. "Ollama连接失败"

**问题**: 无法连接到 `http://localhost:11434`

**解决**:
```bash
# 检查Ollama是否运行
ps aux | grep ollama

# 如果没有，启动它
ollama serve

# 检查端口
lsof -i :11434
```

### 3. "Python版本问题"

**问题**: Python版本不兼容

**解决**:
```bash
# 安装特定版本
brew install python@3.11

# 使用特定版本创建虚拟环境
/usr/local/bin/python3.11 -m venv venv
```

### 4. "Docker未运行"

**问题**: Docker服务未启动

**解决**:
```bash
# 启动Docker Desktop
open /Applications/Docker.app

# 或者不使用Docker，只用本地服务
```

## 🏗️ 项目结构

```
ai-monitor-local/
├── venv/                # Python虚拟环境
├── api/                 # API模块
│   ├── main.py         # FastAPI主程序
│   ├── router.py       # 路由管理
│   └── models.py       # 数据模型
├── core/               # 核心功能
│   ├── llm/           # LLM客户端
│   └── vector/        # 向量数据库
├── logs/              # 日志文件
├── cache/             # 缓存目录
├── .env               # 环境配置
├── requirements.txt   # Python依赖
└── start.sh          # 启动脚本
```

## 🚀 启动服务

### 最简启动

```bash
cd ~/ai-monitor-mini
./start.sh
```

访问:
- API: http://localhost:8000
- 文档: http://localhost:8000/docs

### 完整启动

1. 启动Ollama:
   ```bash
   ollama serve
   ```

2. 启动API服务:
   ```bash
   cd ~/ai-monitor-local
   source venv/bin/activate
   uvicorn api.main:app --reload
   ```

3. （可选）启动Redis:
   ```bash
   docker run -p 6379:6379 redis:7-alpine
   ```

## 📊 性能优化

### 模型选择

根据你的硬件选择合适的模型：

- **内存 < 8GB**: 使用 `phi3:mini` 或 `qwen2.5-coder:1.5b`
- **内存 8-16GB**: 使用 `llama3.2` 或 `qwen2.5-coder:3b`
- **内存 > 16GB**: 可以尝试更大的模型

### 加速技巧

1. **预加载模型**:
   ```bash
   # 在启动时预热模型
   ollama run llama3.2 "test"
   ```

2. **使用更快的模型**:
   ```bash
   # phi3:mini 响应更快
   ollama pull phi3:mini
   ```

3. **调整并发**:
   ```python
   # 在 uvicorn 中设置 workers
   uvicorn app:app --workers 4
   ```

## 🧪 测试验证

运行完整测试：

```bash
python ai-monitor-test-validation.py
```

这会检查：
- ✅ 系统环境
- ✅ 服务状态
- ✅ API功能
- ✅ 性能指标

## 🗑️ 卸载

完全删除系统：

```bash
# 停止服务
pkill ollama
pkill uvicorn

# 删除目录
rm -rf ~/ai-monitor-local
rm -rf ~/ai-monitor-mini

# 删除Docker容器（如果有）
docker rm -f ai-monitor-redis
```

## 💡 提示

1. **不要使用sudo安装Python包**
2. **始终在虚拟环境中工作**
3. **定期更新Ollama模型**
4. **根据需求选择合适的模型大小**

需要帮助？运行 `python diagnose.py` 进行诊断！
