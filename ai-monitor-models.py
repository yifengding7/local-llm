# api/models/request.py
"""
API请求模型定义
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime

class ChatMessage(BaseModel):
    """聊天消息"""
    role: Literal["system", "user", "assistant"]
    content: str
    name: Optional[str] = None
    
class ChatRequest(BaseModel):
    """聊天请求"""
    model: str = Field(default="qwen:8b", description="模型名称")
    messages: List[ChatMessage] = Field(..., description="消息历史")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="生成温度")
    max_tokens: Optional[int] = Field(default=None, ge=1, le=32768, description="最大生成长度")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="Top-p采样")
    top_k: int = Field(default=40, ge=1, description="Top-k采样")
    stream: bool = Field(default=False, description="是否流式返回")
    stop: Optional[List[str]] = Field(default=None, description="停止序列")
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    seed: Optional[int] = Field(default=None, description="随机种子")
    use_rag: bool = Field(default=False, description="是否使用检索增强")
    routing_strategy: str = Field(default="least_loaded", description="路由策略")

    @validator('messages')
    def validate_messages(cls, v):
        if not v:
            raise ValueError("Messages cannot be empty")
        return v

class MonitorRequest(BaseModel):
    """代码监理请求"""
    file_path: str = Field(..., description="文件路径")
    content: Optional[str] = Field(default=None, description="文件内容（可选）")
    rules: Optional[List[str]] = Field(default=None, description="要应用的规则ID列表")
    auto_fix: bool = Field(default=False, description="是否自动修复")
    apply_patch: bool = Field(default=False, description="是否应用补丁")
    git_commit: bool = Field(default=False, description="是否自动提交Git")
    severity_filter: Optional[List[str]] = Field(default=None, description="严重程度过滤")

class VoiceRequest(BaseModel):
    """语音合成请求"""
    text: str = Field(..., max_length=5000, description="要转换的文本")
    voice: str = Field(default="alloy", description="语音类型")
    speed: float = Field(default=1.0, ge=0.25, le=4.0, description="语速")
    format: str = Field(default="mp3", description="音频格式")

class EmbeddingRequest(BaseModel):
    """嵌入请求"""
    input: Union[str, List[str]] = Field(..., description="输入文本")
    model: str = Field(default="nomic-embed-text", description="嵌入模型")
    encoding_format: str = Field(default="float", description="编码格式")

class VectorSearchRequest(BaseModel):
    """向量搜索请求"""
    query: str = Field(..., description="搜索查询")
    vector: Optional[List[float]] = Field(default=None, description="查询向量")
    limit: int = Field(default=10, ge=1, le=100, description="返回结果数量")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="过滤条件")
    alpha: float = Field(default=0.75, ge=0.0, le=1.0, description="混合搜索权重")
    include_vector: bool = Field(default=False, description="是否返回向量")

class ScaffoldRequest(BaseModel):
    """脚手架生成请求"""
    project_name: str = Field(..., regex="^[a-zA-Z][a-zA-Z0-9_-]*$", description="项目名称")
    project_type: str = Field(..., description="项目类型")
    description: str = Field(..., description="项目描述")
    author: str = Field(..., description="作者")
    features: Optional[List[str]] = Field(default=None, description="项目特性")
    use_ai: bool = Field(default=True, description="是否使用AI增强")
    dependencies: Optional[List[str]] = Field(default=None, description="项目依赖")

# api/models/response.py
"""
API响应模型定义
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime

class ChatChoice(BaseModel):
    """聊天选择项"""
    index: int
    message: Dict[str, str]
    finish_reason: Optional[str] = None

class Usage(BaseModel):
    """使用统计"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class ChatResponse(BaseModel):
    """聊天响应"""
    id: str
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(datetime.utcnow().timestamp()))
    model: str = "qwen:8b"
    choices: List[ChatChoice]
    usage: Optional[Usage] = None

class StreamChatResponse(BaseModel):
    """流式聊天响应"""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[Dict[str, Any]]

class Issue(BaseModel):
    """代码问题"""
    file_path: str
    line_number: int
    column: int
    severity: Literal["error", "warning", "info"]
    rule_id: str
    message: str
    suggestion: str
    code_snippet: str

class MonitorResponse(BaseModel):
    """监理响应"""
    file_path: str
    issues: List[Issue]
    severity_counts: Dict[str, int]
    patch: Optional[str] = None
    fixed_count: int = 0
    timestamp: str
    analysis_time_ms: float = 0.0

class EmbeddingData(BaseModel):
    """嵌入数据"""
    object: str = "embedding"
    embedding: List[float]
    index: int

class EmbeddingResponse(BaseModel):
    """嵌入响应"""
    object: str = "list"
    data: List[EmbeddingData]
    model: str
    usage: Usage

class SearchResult(BaseModel):
    """搜索结果"""
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float
    vector: Optional[List[float]] = None

class VectorSearchResponse(BaseModel):
    """向量搜索响应"""
    results: List[SearchResult]
    total_count: int
    query_time_ms: float
    used_vector: bool = True
    used_keyword: bool = True

class ScaffoldResponse(BaseModel):
    """脚手架生成响应"""
    project_path: str
    created_files: List[str]
    project_type: str
    generation_time_s: float
    ai_enhanced: bool = False
    instructions: str

class MetricsResponse(BaseModel):
    """性能指标响应"""
    timestamp: str
    models: Dict[str, Dict[str, Any]]
    task_distribution: Dict[str, int]
    routing_performance: Dict[str, float]
    vector_performance: Dict[str, Any]
    system_resources: Dict[str, float]

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: Literal["healthy", "degraded", "unhealthy"]
    services: Dict[str, str]
    timestamp: str
    version: str = "2.1.0"

class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    message: str
    status_code: int
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    request_id: Optional[str] = None

class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int

class ApiKeyResponse(BaseModel):
    """API密钥响应"""
    api_key: str
    name: str
    scopes: List[str]
    created_at: str
    rate_limit: int