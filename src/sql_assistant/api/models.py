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