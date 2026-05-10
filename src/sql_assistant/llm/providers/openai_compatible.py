"""OpenAI 兼容接口 Provider - 支持 DeepSeek / Doubao / Kimi / Qwen / OpenAI"""

import httpx
from typing import AsyncGenerator, Optional

from ..base import BaseLLMProvider


class OpenAICompatibleProvider(BaseLLMProvider):
    """OpenAI 兼容接口实现"""

    def __init__(self, api_key: str, base_url: str, model: str, provider_name: str = ""):
        super().__init__(api_key, base_url, model)
        self.provider_name = provider_name
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def chat(self, messages: list[dict], temperature: float = 0.1) -> str:
        client = await self._get_client()
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def chat_stream(self, messages: list[dict], temperature: float = 0.1) -> AsyncGenerator[str, None]:
        client = await self._get_client()
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        async with client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        import json
                        data = json.loads(data_str)
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except Exception:
                        continue

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
