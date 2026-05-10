"""Anthropic Claude Provider"""

import httpx
from typing import AsyncGenerator, Optional

from ..base import BaseLLMProvider


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude API 实现"""

    def __init__(self, api_key: str, base_url: str, model: str):
        super().__init__(api_key, base_url, model)
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0),
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    def _convert_messages(self, messages: list[dict]) -> tuple[list[dict], Optional[str]]:
        """将 OpenAI 格式消息转为 Claude 格式"""
        system_content = None
        claude_messages = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_content = content
            elif role == "user":
                claude_messages.append({"role": "user", "content": content})
            elif role == "assistant":
                claude_messages.append({"role": "assistant", "content": content})

        return claude_messages, system_content

    async def chat(self, messages: list[dict], temperature: float = 0.1) -> str:
        client = await self._get_client()
        claude_messages, system = self._convert_messages(messages)

        url = "https://api.anthropic.com/v1/messages"
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "temperature": temperature,
            "messages": claude_messages,
        }
        if system:
            payload["system"] = system

        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"]

    async def chat_stream(self, messages: list[dict], temperature: float = 0.1) -> AsyncGenerator[str, None]:
        client = await self._get_client()
        claude_messages, system = self._convert_messages(messages)

        url = "https://api.anthropic.com/v1/messages"
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "temperature": temperature,
            "messages": claude_messages,
            "stream": True,
        }
        if system:
            payload["system"] = system

        async with client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        import json
                        data = json.loads(data_str)
                        if data.get("type") == "content_block_delta":
                            delta = data.get("delta", {})
                            text = delta.get("text", "")
                            if text:
                                yield text
                    except Exception:
                        continue

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
