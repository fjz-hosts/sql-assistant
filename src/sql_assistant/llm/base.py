"""LLM Provider 抽象基类"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator


class BaseLLMProvider(ABC):
    """LLM Provider 抽象基类"""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    @abstractmethod
    async def chat(self, messages: list[dict], temperature: float = 0.1) -> str:
        """发送对话请求，返回完整响应"""
        ...

    @abstractmethod
    async def chat_stream(self, messages: list[dict], temperature: float = 0.1) -> AsyncGenerator[str, None]:
        """发送流式对话请求"""
        ...
