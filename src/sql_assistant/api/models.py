"""API 数据模型"""

from pydantic import BaseModel, Field
from typing import Optional, Any, List


# ---- Query ----

class QueryRequest(BaseModel):
    question: str = Field(description="自然语言查询问题")
    db_type_override: Optional[str] = Field(default=None, description="临时切换数据库类型")
    conversation_id: Optional[int] = Field(default=None, description="对话ID，用于在已有对话中添加消息")
    page: int = Field(default=1, ge=1, description="结果页码")
    page_size: int = Field(default=100, ge=1, le=1000, description="每页记录数")
    confirmed: bool = Field(default=False, description="用户是否已确认执行")
    sql_hash: Optional[str] = Field(default=None, description="要确认执行的 SQL 哈希，用于验证")
    sql: Optional[str] = Field(default=None, description="用户确认后要执行的 SQL 语句（confirmed=True 时使用）")


class SQLPreviewResponse(BaseModel):
    """SQL 预览响应"""
    success: bool
    sql: str = ""
    sql_hash: str = ""
    requires_confirmation: bool = False
    confirmation_reason: str = ""
    warning: str = ""
    risk_level: str = "none"
    error: Optional[str] = None


class QueryResponse(BaseModel):
    success: bool
    question: str = ""
    sql: str = ""
    result: Optional[dict] = None
    error: Optional[str] = None
    history_id: Optional[int] = None
    conversation_id: Optional[int] = None
    pagination: Optional[dict] = None


# ---- Conversation ----

class ConversationRequest(BaseModel):
    title: Optional[str] = Field(default="", description="对话标题")


class ConversationUpdateRequest(BaseModel):
    title: str = Field(description="新的对话标题")


class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: str = ""
    updated_at: str = ""
    message_count: int = 0


class ConversationDetailResponse(BaseModel):
    id: int
    title: str
    created_at: str = ""
    updated_at: str = ""
    messages: list["HistoryRecord"] = Field(default_factory=list)


class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]
    total: int
    limit: int
    offset: int


# ---- Config: LLM ----

class LLMConfigRequest(BaseModel):
    name: str
    provider: str  # deepseek, doubao, kimi, qwen, gemini, claude, openai
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    enabled: bool = True


class LLMConfigResponse(BaseModel):
    name: str
    provider: str
    model: str
    enabled: bool
    api_key_masked: str = ""  # 只显示后4位


# ---- Config: Database ----

class DatabaseConfigRequest(BaseModel):
    name: str
    db_type: str  # mysql, sqlserver, postgresql, redis, mongodb
    host: str = "localhost"
    port: int = 0
    user: str = ""
    password: str = ""
    database: str = ""
    enabled: bool = True


class DatabaseConfigResponse(BaseModel):
    name: str
    db_type: str
    host: str
    port: int
    user: str
    database: str
    enabled: bool


class TestConnectionRequest(BaseModel):
    """测试连接请求 - 可传完整配置或只传名称"""
    name: Optional[str] = None
    config: Optional[DatabaseConfigRequest] = None


class TestLLMConnectionRequest(BaseModel):
    """测试 LLM 连接请求"""
    name: Optional[str] = None
    config: Optional[LLMConfigRequest] = None


class TestConnectionResponse(BaseModel):
    success: bool
    message: str


# ---- Config: Settings ----

class AppSettingsResponse(BaseModel):
    active_llm: str = ""
    active_database: str = ""
    max_history_rows: int = 1000
    llm_providers: list[LLMConfigResponse] = Field(default_factory=list)
    databases: list[DatabaseConfigResponse] = Field(default_factory=list)


# ---- History ----

class HistoryRecord(BaseModel):
    id: int
    conversation_id: Optional[int] = None
    question: str
    sql: str
    result_json: Optional[str] = None
    db_type: str = ""
    llm_provider: str = ""
    success: bool = True
    error_message: str = ""
    created_at: str = ""


class HistoryListResponse(BaseModel):
    records: list[HistoryRecord]
    total: int
    limit: int
    offset: int


# ---- Backup ----

class BackupRequest(BaseModel):
    """备份请求模型"""
    backup_type: str = Field(default="full", description="备份类型: full(全量备份) / incremental(增量备份)")
    tables: Optional[List[str]] = Field(default=None, description="要备份的表名列表，为空则备份所有表")
    include_schema: bool = Field(default=True, description="是否包含表结构")
    include_data: bool = Field(default=True, description="是否包含数据")


class BackupResponse(BaseModel):
    """备份响应模型"""
    success: bool
    message: str
    backup_id: str = ""
    backup_path: str = ""
    tables_backed_up: List[str] = Field(default_factory=list)
    total_records: int = 0
    backup_size: int = 0  # bytes
    backup_time: str = ""


class BackupInfoResponse(BaseModel):
    """备份信息响应模型"""
    backup_id: str
    backup_type: str
    db_type: str = ""
    db_name: str = ""
    tables: List[str] = Field(default_factory=list)
    record_count: int = 0
    backup_time: str = ""
    file_size: int = 0  # bytes


class BackupListResponse(BaseModel):
    """备份列表响应模型"""
    backups: List[BackupInfoResponse]
    total: int


class RestoreRequest(BaseModel):
    """恢复备份请求模型"""
    backup_id: str = Field(description="要恢复的备份ID")
    restore_schema: bool = Field(default=False, description="是否重建表结构（谨慎使用，会删除现有表）")
    restore_data: bool = Field(default=True, description="是否恢复数据")
    tables: Optional[List[str]] = Field(default=None, description="指定要恢复的表，为空则恢复所有表")


class RestoreResponse(BaseModel):
    """恢复备份响应模型"""
    success: bool
    message: str
    backup_id: str = ""
    tables_restored: List[str] = Field(default_factory=list)
    total_records: int = 0


# ---- Templates ----

class TemplateRequest(BaseModel):
    """模板请求模型"""
    name: str = Field(description="模板名称")
    description: Optional[str] = Field(default="", description="模板描述")
    sql: str = Field(description="SQL模板内容")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签列表")

class TemplateResponse(BaseModel):
    """模板响应模型"""
    id: int
    name: str
    description: str = ""
    sql: str
    tags: List[str] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

class TemplateListResponse(BaseModel):
    """模板列表响应模型"""
    templates: List[TemplateResponse]
    total: int


# ---- Export ----

class ExportRequest(BaseModel):
    """导出请求模型"""
    columns: List[str] = Field(description="列名列表")
    rows: List[List[Any]] = Field(description="数据行列表")
    format: str = Field(default="csv", description="导出格式: csv / json / excel")

class ExportResponse(BaseModel):
    """导出响应模型"""
    success: bool
    format: str = ""
    content: str = ""
    content_type: str = ""
    filename: str = ""
    row_count: int = 0
    error: Optional[str] = None


# ---- Explain Plan ----

class ExplainRequest(BaseModel):
    """执行计划分析请求模型"""
    sql: str = Field(description="要分析的SQL语句")
    analyze: bool = Field(default=True, description="是否执行ANALYZE获取实际执行时间")


class ExplainPlanNode(BaseModel):
    """执行计划节点"""
    id: int = Field(default=0, description="节点ID")
    parent_id: Optional[int] = Field(default=None, description="父节点ID")
    node_type: str = Field(default="", description="节点类型")
    table_name: Optional[str] = Field(default=None, description="表名")
    access_type: Optional[str] = Field(default=None, description="访问类型")
    key: Optional[str] = Field(default=None, description="使用的索引")
    rows: Optional[int] = Field(default=None, description="估计扫描行数")
    cost: Optional[float] = Field(default=None, description="估计成本")
    actual_time: Optional[float] = Field(default=None, description="实际执行时间(ms)")
    actual_rows: Optional[int] = Field(default=None, description="实际返回行数")
    extra: Optional[str] = Field(default=None, description="额外信息")
    children: List["ExplainPlanNode"] = Field(default_factory=list, description="子节点")


class ExplainResponse(BaseModel):
    """执行计划分析响应模型"""
    success: bool
    plan_id: Optional[int] = Field(default=None, description="保存的计划ID")
    sql: str = ""
    db_type: str = ""
    db_name: str = ""
    plan_tree: Optional[ExplainPlanNode] = Field(default=None, description="执行计划树")
    plan_text: str = ""
    estimated_cost: float = 0.0
    estimated_rows: int = 0
    actual_time_ms: float = 0.0
    warnings: List[str] = Field(default_factory=list, description="警告信息")
    suggestions: List[str] = Field(default_factory=list, description="优化建议")
    is_slow_query: bool = False
    error: Optional[str] = None


class ExplainHistoryRecord(BaseModel):
    """执行计划历史记录"""
    id: int
    sql: str
    db_type: str
    db_name: str
    estimated_cost: float
    estimated_rows: int
    actual_time_ms: float
    warnings: List[str]
    suggestions: List[str]
    is_slow_query: bool
    created_at: str


class ExplainHistoryListResponse(BaseModel):
    """执行计划历史列表响应"""
    records: List[ExplainHistoryRecord]
    total: int
    limit: int
    offset: int


class ExplainStatsResponse(BaseModel):
    """执行计划统计响应"""
    total_plans: int
    slow_query_count: int
    average_cost: float
    max_cost: float