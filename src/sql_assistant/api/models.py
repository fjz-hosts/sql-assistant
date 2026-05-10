"""API 数据模型"""

from pydantic import BaseModel, Field
from typing import Optional, Any


# ---- Query ----

class QueryRequest(BaseModel):
    question: str = Field(description="自然语言查询问题")
    db_type_override: Optional[str] = Field(default=None, description="临时切换数据库类型")


class QueryResponse(BaseModel):
    success: bool
    question: str = ""
    sql: str = ""
    result: Optional[dict] = None
    error: Optional[str] = None
    history_id: Optional[int] = None


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
