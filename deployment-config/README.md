# AI监理系统 v2.1 部署配置

## 📁 目录结构

```
deployment-config/
├── README.md                           # 本文件 - 目录说明
├── ai-monitor-v2.1-deployment.yaml   # 主部署配置文件
├── environment-config.yaml           # 环境管理配置
├── architecture-compliance.yaml      # 架构合规检查
├── validation-checklist.yaml        # 验证清单
├── DEPLOYMENT-GUIDE.md              # 详细部署指南
└── scripts/                         # 支持脚本
    ├── auto_review.sh               # 自动代码审查
    ├── pre_plan_gatekeeper.sh      # 计划守门员
    ├── auto_format.sh              # 自动格式化
    └── notify_handler.sh           # 通知处理
```

## 📋 文件说明

### 核心配置文件

#### 1. `ai-monitor-v2.1-deployment.yaml`
- **作用**: 主部署配置文件
- **内容**: 
  - 完整的6层架构定义
  - 2025年最新技术栈版本约束
  - 5个部署阶段详细规划
  - M3 Max硬件优化配置
  - 企业级功能集成
- **使用**: 部署流程的核心指导文件

#### 2. `environment-config.yaml`
- **作用**: 环境管理配置
- **内容**:
  - 工业级Nix环境管理
  - 容器化部署配置
  - 硬件优化设置
  - 性能监控配置
- **使用**: 环境搭建和优化

#### 3. `architecture-compliance.yaml`
- **作用**: 架构合规检查
- **内容**:
  - 100%架构蓝图合规验证
  - 自动化检查脚本
  - 修复建议系统
  - 持续监控配置
- **使用**: 确保部署符合架构要求

#### 4. `validation-checklist.yaml`
- **作用**: 验证清单
- **内容**:
  - 85个详细验证检查点
  - 性能基准测试
  - 企业级功能验证
  - 安全性检查
- **使用**: 部署质量保证

#### 5. `DEPLOYMENT-GUIDE.md`
- **作用**: 详细部署指南
- **内容**:
  - 完整的部署流程说明
  - 故障排除指南
  - 性能优化建议
  - 监控和维护说明
- **使用**: 部署操作手册

### 支持脚本

#### 1. `scripts/auto_review.sh`
- **作用**: 自动代码审查
- **功能**:
  - 代码质量检查
  - 安全性扫描
  - 格式验证
  - AI辅助审查
- **触发**: Claude CLI Stop Hook

#### 2. `scripts/pre_plan_gatekeeper.sh`
- **作用**: 计划守门员
- **功能**:
  - 任务完成质量检查
  - 项目状态验证
  - 合规性预检
- **触发**: Claude CLI PreToolUse Hook

#### 3. `scripts/auto_format.sh`
- **作用**: 自动格式化
- **功能**:
  - 代码自动格式化
  - 保持代码风格一致
  - 检查语法错误
- **触发**: Claude CLI PostToolUse Hook

#### 4. `scripts/notify_handler.sh`
- **作用**: 通知处理
- **功能**:
  - 重要变更实时提醒
  - 系统状态监控
  - 服务健康检查
- **触发**: Claude CLI Notification Hook

## 🚀 使用方法

### 1. 快速开始
```bash
# 进入部署配置目录
cd "/Users/imac/Documents/编程/项目/本地llm项目/deployment-config"

# 阅读部署指南
cat DEPLOYMENT-GUIDE.md

# 开始部署
./scripts/deploy.sh  # 需要根据指南创建
```

### 2. 验证部署
```bash
# 运行架构合规检查
python3 -c "
import yaml
with open('architecture-compliance.yaml', 'r') as f:
    config = yaml.safe_load(f)
    print('架构合规检查配置加载成功')
"

# 运行验证清单
python3 -c "
import yaml
with open('validation-checklist.yaml', 'r') as f:
    checklist = yaml.safe_load(f)
    print(f'验证清单包含 {len(checklist.get(\"pre_deployment_validation\", {}).get(\"environment_checks\", []))} 个环境检查')
"
```

### 3. 配置Hook系统
```bash
# 更新Claude配置以使用新的脚本路径
# 编辑 ~/.claude/settings.local.json
# 更新脚本路径为:
# "/Users/imac/Documents/编程/项目/本地llm项目/deployment-config/scripts/auto_review.sh"
```

## 📊 配置概览

### 版本约束
- Python: 3.13
- FastAPI: 0.116.1
- Pydantic: 2.11.7
- Uvicorn: 0.35.0
- Ollama: 0.3.0

### 架构层次
1. 前端展示层 (🖥️)
2. API服务层 (🔌)
3. 核心引擎层 (⚙️)
4. 极致性能层 (🔥)
5. 基础设施层 (🏗️)
6. MCP集成层 (🔗)

### 性能目标
- 查询延迟: <50ms
- 向量容量: 1000万+
- 并发用户: 无限制
- 内存带宽: 400GB/s

## 🔧 自定义配置

### 修改部署配置
```bash
# 编辑主配置文件
vi ai-monitor-v2.1-deployment.yaml

# 修改环境配置
vi environment-config.yaml

# 调整合规检查规则
vi architecture-compliance.yaml
```

### 添加验证检查
```bash
# 编辑验证清单
vi validation-checklist.yaml

# 添加新的检查项到相应分类
```

## 🛠️ 故障排除

### 常见问题
1. **YAML格式错误**: 使用yamllint检查语法
2. **路径问题**: 确保所有路径都是绝对路径
3. **权限问题**: 确保脚本有执行权限
4. **依赖缺失**: 检查所有必要工具是否安装

### 检查命令
```bash
# 检查YAML语法
yamllint *.yaml

# 检查脚本权限
ls -la scripts/

# 验证配置完整性
python3 -c "
import yaml
import os
for file in ['ai-monitor-v2.1-deployment.yaml', 'environment-config.yaml', 'architecture-compliance.yaml', 'validation-checklist.yaml']:
    if os.path.exists(file):
        with open(file, 'r') as f:
            yaml.safe_load(f)
        print(f'✅ {file} 格式正确')
    else:
        print(f'❌ {file} 不存在')
"
```

## 📞 支持

如有问题，请参考：
1. `DEPLOYMENT-GUIDE.md` - 详细部署指南
2. 各配置文件中的注释说明
3. 脚本文件中的使用说明

## 🎯 下一步

1. 阅读 `DEPLOYMENT-GUIDE.md`
2. 根据环境需求调整配置文件
3. 运行架构合规检查
4. 执行部署流程
5. 进行完整验证

---

**注意**: 这是一个完整的企业级部署方案，请确保在生产环境中使用前进行充分测试。
