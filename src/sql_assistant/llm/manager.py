"""LLM Manager - 统一管理所有 Provider"""

from typing import AsyncGenerator, Optional

from ..config import get_config_manager
from ..settings import LLMProviderConfig
from .base import BaseLLMProvider
from .providers.openai_compatible import OpenAICompatibleProvider
from .providers.gemini import GeminiProvider
from .providers.claude import ClaudeProvider


class LLMManager:
    """LLM Provider 管理器"""

    def __init__(self):
        self._providers: dict[str, BaseLLMProvider] = {}

    def _create_provider(self, config: LLMProviderConfig) -> BaseLLMProvider:
        """根据配置创建对应的 Provider 实例"""
        if config.is_openai_compatible():
            return OpenAICompatibleProvider(
                api_key=config.api_key,
                base_url=config.get_base_url(),
                model=config.get_model(),
                provider_name=config.provider,
            )
        elif config.provider == "gemini":
            return GeminiProvider(
                api_key=config.api_key,
                base_url=config.get_base_url(),
                model=config.get_model(),
            )
        elif config.provider == "claude":
            return ClaudeProvider(
                api_key=config.api_key,
                base_url=config.get_base_url(),
                model=config.get_model(),
            )
        else:
            raise ValueError(f"不支持的 Provider: {config.provider}")

    def get_provider(self, config: LLMProviderConfig) -> BaseLLMProvider:
        """获取或创建 Provider (带缓存)"""
        key = config.name
        if key not in self._providers:
            self._providers[key] = self._create_provider(config)
        return self._providers[key]

    async def chat(self, messages: list[dict], temperature: float = 0.1) -> str:
        """使用当前激活的 LLM 发送对话请求"""
        config = get_config_manager().get_active_llm()
        if not config:
            raise ValueError("未配置 LLM，请先在设置中添加 LLM 提供商")
        provider = self.get_provider(config)
        return await provider.chat(messages, temperature)

    async def chat_stream(self, messages: list[dict], temperature: float = 0.1) -> AsyncGenerator[str, None]:
        """使用当前激活的 LLM 发送流式对话"""
        config = get_config_manager().get_active_llm()
        if not config:
            raise ValueError("未配置 LLM，请先在设置中添加 LLM 提供商")
        provider = self.get_provider(config)
        async for chunk in provider.chat_stream(messages, temperature):
            yield chunk

    async def close_all(self):
        """关闭所有 Provider 连接"""
        for provider in self._providers.values():
            if hasattr(provider, "close"):
                await provider.close()
        self._providers.clear()


# 全局单例
_llm_manager: Optional[LLMManager] = None


def get_llm_manager() -> LLMManager:
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager
