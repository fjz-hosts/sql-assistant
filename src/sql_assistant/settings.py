"""配置数据模型"""

from pydantic import BaseModel, Field
from typing import Optional, Literal


# 默认 Base URL 映射
DEFAULT_BASE_URLS: dict[str, str] = {
    "deepseek": "https://api.deepseek.com/v1",
    "doubao": "https://ark.cn-beijing.volces.com/api/v3",
    "kimi": "https://api.moonshot.cn/v1",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "openai": "https://api.openai.com/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta",
    "claude": "https://api.anthropic.com/v1",
    "glm": "https://open.bigmodel.cn/api/paas/v4",
    "minimax": "https://api.minimaxi.com/anthropic/v1",
    "siliconflow": "https://api.siliconflow.cn/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "grok": "https://api.x.ai/v1",
    "tencent": "https://tokenhub.tencentmaas.com/v1",
    "mimo": "https://api.xiaomimimo.com/v1",
    "ollama": "http://localhost:11434/v1",
}

# 默认模型映射（2025-2026最新版本）
DEFAULT_MODELS: dict[str, str] = {
    "deepseek": "deepseek-v4-pro",
    "doubao": "doubao-seed-2-0-pro-260215",
    "kimi": "kimi-k2.6",
    "qwen": "qwen3.6-max-preview",
    "openai": "gpt-5.5",
    "gemini": "gemini-3.1-pro-preview",
    "claude": "claude-opus-4-7",
    "glm": "glm-5.1",
    "minimax": "MiniMax-M2.7",
    "siliconflow": "deepseek-ai/DeepSeek-V3.2",
    "openrouter": "deepseek/deepseek-v4-pro",
    "grok": "grok-4.20-reasoning",
    "tencent": "hy3-preview",
    "mimo": "mimo-v2.5-pro",
    "ollama": "llama3.3",
}

# 各提供商支持的模型列表（2025-2026最新）
PROVIDER_MODELS: dict[str, list[str]] = {
    # === 已支持的提供商 ===
    "deepseek": [
        "deepseek-v4-pro",
        "deepseek-v4-flash",
    ],
    "doubao": [
        "doubao-seed-2-0-pro-260215",
        "doubao-seed-2-0-lite-260215",
        "doubao-seed-2-0-mini-260215",
        "doubao-seed-1-8-251228",
    ],
    "kimi": [
        "kimi-k2.6",
        "kimi-k2.5",
        "kimi-k2-thinking",
    ],
    "qwen": [
        "qwen3.6-max-preview",
        "qwen3.6-plus",
        "qwen3.6-plus-2026-04-02",
        "qwen3.6-flash",
        "qwen3.6-flash-2026-04-16",
        "qwen3.6-35b-a3b",
        "qwen3.5-flash",
        "qwen3.5-plus",
        "qwen3-max",
        "qwen3-vl-plus",
    ],
    "openai": [
        "gpt-5.5",
        "gpt-5.4-pro",
        "gpt-5.4-mini",
        "gpt-5.4-nano",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4.1",
        "gpt-4.1-mini",
        "gpt-4",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
        "o1-preview",
        "o1-mini",
    ],
    "gemini": [
        "gemini-3.1-pro-preview",
        "gemini-3-flash-preview",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.5-pro",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-1.0-pro",
    ],
    "claude": [
        "claude-opus-4-7",
        "claude-opus-4-6",
        "claude-sonnet-4-6",
        "claude-sonnet-4-5",
        "claude-haiku-4-5",
        "claude-3-sonnet",
        "claude-3-opus",
        "claude-3-haiku",
        "claude-2.1",
        "claude-2",
    ],
    # === 尚未支持的提供商（待扩展）===
    "glm": [
        "glm-5.1",
        "glm-5v-turbo",
        "glm-5",
        "glm-4.7",
        "glm-4.7-flashx",
        "glm-4.7-flash",
        "glm-4.6",
        "glm-4.6v",
        "glm-4.6v-flash",
    ],
    "minimax": [
        "MiniMax-M2.7",
    ],
    "siliconflow": [
        "deepseek-ai/DeepSeek-V3.2",
        "deepseek-ai/DeepSeek-R1",
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        "Qwen/Qwen3-VL-32B-Instruct",
        "Pro/moonshotai/Kimi-K2.5",
        "THUDM/GLM-4.1V-9B-Thinking",
        "THUDM/GLM-Z1-Rumination-32B-0414",
    ],
    "openrouter": [
        "deepseek/deepseek-v4-pro",
        "deepseek/deepseek-v4-flash",
    ],
    "grok": [
        "grok-4.20-reasoning",
        "grok-4.20",
        "grok-4.20-multi-agent",
        "grok-4-1-fast-reasoning",
        "grok-4-1-fast-non-reasoning",
        "grok-code-fast-1",
    ],
    "tencent": [
        "hy3-preview",
    ],
    "mimo": [
        "mimo-v2.5-pro",
        "mimo-v2.5",
    ],
    "ollama": [
        "llama3.3",
        "gemma3",
        "deepseek-r1",
    ],
}


class LLMProviderConfig(BaseModel):
    """LLM 提供商配置"""
    name: str = Field(description="配置名称，如 '我的DeepSeek'")
    provider: Literal[
        "deepseek", "doubao", "kimi", "qwen", "gemini", "claude", "openai",
        "glm", "minimax", "siliconflow", "openrouter", "grok", "tencent", "mimo", "ollama"
    ] = Field(description="LLM 提供商类型")
    api_key: str = Field(default="", description="API Key")
    base_url: str = Field(default="", description="API 基础URL（OpenAI兼容接口自动填充，可覆盖）")
    model: str = Field(default="", description="模型名称")
    enabled: bool = Field(default=True, description="是否启用")

    def get_base_url(self) -> str:
        return self.base_url or DEFAULT_BASE_URLS.get(self.provider, "")

    def get_model(self) -> str:
        return self.model or DEFAULT_MODELS.get(self.provider, "")

    def is_openai_compatible(self) -> bool:
        """除 Claude、Gemini 和 MiniMax 外都是 OpenAI 兼容接口"""
        return self.provider not in ("claude", "gemini", "minimax")


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


class ScheduledBackupConfig(BaseModel):
    """定时备份配置"""
    enabled: bool = Field(default=False, description="是否启用定时备份")
    hour: int = Field(default=2, description="每天几点执行备份（0-23）")
    minute: int = Field(default=0, description="分钟数（0-59）")
    backup_type: str = Field(default="full", description="备份类型: full / incremental")
    retention_count: int = Field(default=7, description="最多保留备份数量，0表示不限制")
    include_schema: bool = Field(default=True, description="是否包含表结构")
    include_data: bool = Field(default=True, description="是否包含数据")


class AppSettings(BaseModel):
    """应用全局设置"""
    llm_providers: list[LLMProviderConfig] = Field(default_factory=list)
    databases: list[DatabaseConfig] = Field(default_factory=list)
    active_llm: str = Field(default="", description="当前激活的 LLM 配置名称")
    active_database: str = Field(default="", description="当前激活的数据库配置名称")
    max_history_rows: int = Field(default=1000, description="最大历史记录数")
    theme: Literal["light", "dark", "auto"] = Field(default="auto")
    scheduled_backup: ScheduledBackupConfig = Field(default_factory=ScheduledBackupConfig, description="定时备份配置")
