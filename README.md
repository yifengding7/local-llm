# 本地LLM项目 - AI监理系统 v2.2

> **统一架构 | 高性能 | 企业级**  
> 集成AI监理系统、Claude Code集成系统(CCIS)和多语言性能层的现代化本地LLM平台

![Project Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Version](https://img.shields.io/badge/Version-2.2.0-blue)
![Python](https://img.shields.io/badge/Python-3.12%2B-yellow)
![Go](https://img.shields.io/badge/Go-1.22%2B-cyan)
![Rust](https://img.shields.io/badge/Rust-1.70%2B-orange)

## 🚀 项目概述

本项目是一个多语言、多层次的本地AI监理系统，通过统一架构整合了以下核心组件：

- **AI监理系统 v2.2**：基于FastAPI 0.116.1的现代化Python核心服务
- **Claude Code集成系统(CCIS)**：统一的AI代码生成和分析工具
- **多语言性能层**：Go高并发API + Rust零延迟计算引擎  
- **企业级控制中心**：统一服务管理和监控平台
- **容器化部署**：Docker Compose完整服务编排

## 🚀 快速开始

### 前置要求

- Docker 和 Docker Compose
- Python 3.12+
- Poetry (Python包管理)

### 一键启动

```bash
# 启动所有服务
./control_center.sh

# 或使用Docker Compose
docker compose up -d
```

### 验证部署

```bash
# 检查核心服务状态
curl http://localhost:8000/health    # Python核心服务
curl http://localhost:11434/health   # Ollama LLM引擎  
curl http://localhost:8080/v1/meta   # Weaviate向量库
```

## 📋 系统架构

### 核心服务层
- **Python核心服务** (端口8000): FastAPI 0.116.1主API服务
- **Ollama LLM** (端口11434): 本地大语言模型推理引擎
- **Weaviate** (端口8080): 向量数据库和语义搜索

### 性能加速层
- **Go微服务** (端口3001): 高并发API处理
- **Rust引擎** (端口3002): 零延迟计算引擎

### AI集成层
- **Claude模拟器**: 智能代码生成和分析
- **MCP工具**: Model Context Protocol集成接口
- **终端桥接**: 安全命令执行

## 📁 目录结构

```
本地llm项目/
├── ai-monitor/                    # 统一AI监理系统
│   ├── core/                      # Python核心服务
│   ├── performance/go/            # Go微服务
│   ├── performance/rust/          # Rust引擎
│   └── tests/                     # 测试套件
├── claude_code/                   # Claude Code集成
│   ├── claude_simulator.py       # 核心模拟器
│   └── mcp_tools/                 # MCP工具集
├── control_center.sh              # 统一控制脚本
├── docker-compose.yml             # 服务编排
├── pyproject.toml                 # Python配置
└── monitoring/logs/               # 日志目录
```

## 🔧 使用控制中心

```bash
# 启动控制中心
./control_center.sh

# 主要功能:
# 1) 显示服务状态
# 2) 启动所有服务 (Docker)
# 3) 停止所有服务
# 4) 启动开发模式API
# 5) Claude Code功能
```

## 🧪 测试验证

```bash
# 安装依赖
poetry install

# 运行测试
poetry run pytest

# 代码质量检查
poetry run ruff check .
```

## 🛠️ 技术栈

- **Python**: FastAPI 0.116.1, Pydantic 2.11.7, Uvicorn 0.35.0
- **Go**: 高并发API服务
- **Rust**: 零延迟计算引擎
- **Docker**: 容器化部署
- **Weaviate**: 向量数据库
- **Ollama**: 本地LLM引擎

## 📊 监控和日志

- **健康检查**: 所有服务提供 `/health` 端点
- **日志管理**: 集中在 `monitoring/logs/` 目录
- **实时监控**: 通过控制中心查看服务状态
- **性能指标**: Prometheus集成支持

## 🔒 安全特性

- 本地部署，数据不外传
- Docker容器隔离
- JWT认证支持
- 环境变量配置管理

## 📄 版本信息

**当前版本**: v2.2.0  
**发布日期**: 2025年1月  
**状态**: 生产就绪

### v2.2.0 更新内容
- ✅ 统一项目架构
- ✅ 升级最新技术栈
- ✅ 集成Claude Code系统
- ✅ 优化性能层
- ✅ 完善监控体系

---

> 🚀 **企业级本地LLM解决方案** - 高性能、安全、可扩展