"""配置数据模型"""

from pydantic import BaseModel, Field
from typing import Optional, Literal


class LLMProviderConfig(BaseModel):
    """LLM 提供商配置"""
    name: str = Field(description="配置名称，如 '我的DeepSeek'")
    provider: Literal["deepseek", "doubao", "kimi", "qwen", "gemini", "claude", "openai"] = Field(
        description="LLM 提供商类型"
    )
    api_key: str = Field(default="", description="API Key")
    base_url: str = Field(default="", description="API 基础URL（OpenAI兼容接口自动填充，可覆盖）")
    model: str = Field(default="", description="模型名称")
    enabled: bool = Field(default=True, description="是否启用")

    # 默认 Base URL 映射
    DEFAULT_BASE_URLS: dict[str, str] = {
        "deepseek": "https://api.deepseek.com/v1",
        "doubao": "https://api.doubao.com/v1",
        "kimi": "https://api.moonshot.cn/v1",
        "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "openai": "https://api.openai.com/v1",
    }

    # 默认模型映射
    DEFAULT_MODELS: dict[str, str] = {
        "deepseek": "deepseek-chat",
        "doubao": "Doubao-5.0",
        "kimi": "kimi-v",
        "qwen": "qwen3.5-turbo",
        "openai": "gpt-4o",
    }

    def get_base_url(self) -> str:
        return self.base_url or self.DEFAULT_BASE_URLS.get(self.provider, "")

    def get_model(self) -> str:
        return self.model or self.DEFAULT_MODELS.get(self.provider, "")

    def is_openai_compatible(self) -> bool:
        """除 Gemini 和 Claude 外都是 OpenAI 兼容接口"""
        return self.provider not in ("gemini", "claude")


class DatabaseConfig(BaseModel):
    """数据库连接配置"""
    name: str = Field(description="连接名称，如 '生产MySQL'")
    db_type: Literal["mysql", "sqlserver", "postgresql", "redis", "mongodb"] = Field(
        description="数据库类型"
    )
    host: str = Field(default="localhost", description="主机地址")
    port: int = Field(default=0, description="端口")
    user: str = Field(default="", description="用户名")
    password: str = Field(default="", description="密码")
    database: str = Field(default="", description="数据库名")
    enabled: bool = Field(default=True, description="是否启用")

    DEFAULT_PORTS: dict[str, int] = {
        "mysql": 3306,
        "sqlserver": 1433,
        "postgresql": 5432,
        "redis": 6379,
        "mongodb": 27017,
    }

    def get_port(self) -> int:
        return self.port or self.DEFAULT_PORTS.get(self.db_type, 0)


class AppSettings(BaseModel):
    """应用全局设置"""
    llm_providers: list[LLMProviderConfig] = Field(default_factory=list)
    databases: list[DatabaseConfig] = Field(default_factory=list)
    active_llm: str = Field(default="", description="当前激活的 LLM 配置名称")
    active_database: str = Field(default="", description="当前激活的数据库配置名称")
    max_history_rows: int = Field(default=1000, description="最大历史记录数")
    theme: Literal["light", "dark", "auto"] = Field(default="auto")
