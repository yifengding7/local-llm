# 本地LLM项目 - 系统架构图

## 控制中心架构

```mermaid
graph TB
    subgraph "控制中心 Control Center"
        CC[control_center.sh<br/>主控制脚本]
        CC --> MM[主菜单]
        
        MM --> SM[服务管理]
        MM --> CM[Claude Code]
        MM --> LM[日志查看]
        MM --> AM[高级功能]
        
        SM --> |启动| AS[所有服务]
        SM --> |停止| SS[停止服务]
        SM --> |状态| VS[查看状态]
        
        CM --> CP[创建项目]
        CM --> CA[分析代码]
        CM --> CW[编写代码]
        CM --> BR[批量重构]
    end
    
    subgraph "AI监理系统 v2.1"
        PC[Python核心<br/>:8000] 
        OL[Ollama LLM<br/>:11434]
        WV[Weaviate<br/>:8080]
        GO[Go API<br/>:3001]
        RS[Rust引擎<br/>:3002]
    end
    
    subgraph "Claude-Code集成系统"
        CS[claude_simulator.py]
        MT[claude_code_mcp_tool.py]
        CH[claude_helper.sh]
        TB[claude_terminal_bridge.py]
    end
    
    subgraph "辅助工具"
        HC[health_check.py<br/>健康检查]
        DG[diagnose.py<br/>系统诊断]
        TV[test_validation.py<br/>测试验证]
    end
    
    subgraph "输出目录"
        CO[~/claude-code-output<br/>代码输出]
        LG[logs/<br/>日志文件]
        PD[.pids/<br/>进程ID]
    end
    
    CC --> AS
    AS --> PC & OL & WV & GO & RS
    
    CM --> CS
    CS --> MT
    MT --> TB
    TB --> CO
    
    AM --> HC & DG & TV
    
    LM --> LG
    SM --> PD
```

## 服务依赖关系

```mermaid
graph LR
    subgraph "核心依赖"
        PY[Python 3.8+]
        DK[Docker]
        HB[Homebrew]
    end
    
    subgraph "语言环境"
        GO_ENV[Go 1.19+]
        RUST[Rust/Cargo]
        NODE[Node.js<br/>可选]
    end
    
    subgraph "AI/ML工具"
        OLLAMA[Ollama]
        WEAVIATE[Weaviate<br/>Docker镜像]
    end
    
    PY --> PC[Python核心服务]
    GO_ENV --> GO_API[Go闪电API]
    RUST --> RUST_ENGINE[Rust零延迟引擎]
    OLLAMA --> LLM[LLM服务]
    DK --> WEAVIATE
    WEAVIATE --> VDB[向量数据库]
```

## 数据流向

```mermaid
flowchart LR
    User[用户] --> CC[控制中心]
    
    CC --> |管理命令| Services[服务组]
    CC --> |代码任务| Claude[Claude Code]
    
    Services --> API[API响应]
    Claude --> Code[生成代码]
    
    API --> Output[输出结果]
    Code --> Files[文件系统]
    
    Output --> User
    Files --> User
```

## 启动流程

```mermaid
sequenceDiagram
    participant U as 用户
    participant CC as 控制中心
    participant S as 服务
    participant L as 日志
    
    U->>CC: 运行 llm-control
    CC->>CC: 初始化检查
    CC->>U: 显示主菜单
    U->>CC: 选择"启动所有服务"
    
    CC->>S: 启动Ollama
    S-->>L: 写入ollama.log
    CC->>S: 启动Python核心
    S-->>L: 写入core-service.log
    CC->>S: 启动Weaviate
    CC->>S: 启动Go API
    CC->>S: 启动Rust引擎
    
    S->>CC: 返回启动状态
    CC->>U: 显示服务状态
```

## 文件组织结构

```
/Users/imac/Documents/编程/项目/本地llm项目/
│
├── 🎮 控制中心
│   ├── control_center.sh          # 主控制脚本
│   ├── install_control_center.sh  # 安装脚本
│   └── service_groups.conf        # 服务配置
│
├── 🤖 AI监理系统
│   └── ai-monitor-v2/
│       ├── core/                  # Python核心
│       ├── performance/           # Go/Rust组件
│       └── logs/                  # 服务日志
│
├── 🔧 Claude Code集成
│   ├── claude_simulator.py        # 模拟器
│   ├── claude_code_mcp_tool.py   # MCP接口
│   ├── claude_helper.sh          # CLI助手
│   └── claude_terminal_bridge.py  # 终端桥接
│
├── 🩺 诊断工具
│   ├── health_check.py           # 健康检查
│   ├── diagnose.py               # 系统诊断
│   └── test_validation.py        # 测试验证
│
├── 📚 文档
│   ├── README.md                 # 项目说明
│   ├── CONTROL_CENTER_README.md  # 控制中心文档
│   └── *.md                      # 其他文档
│
└── 📂 输出目录
    ├── ~/claude-code-output/     # 代码输出
    └── .pids/                    # 进程管理
```

---

这个架构图展示了整个系统的组织结构和相互关系。控制中心是所有组件的统一入口。
