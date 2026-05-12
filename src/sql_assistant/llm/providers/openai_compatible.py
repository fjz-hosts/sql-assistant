"""OpenAI 兼容接口 Provider - 支持 DeepSeek / Doubao / Kimi / Qwen / OpenAI"""

import httpx
from typing import AsyncGenerator, Optional

from ..base import BaseLLMProvider
from ..retry import async_retry
from ..exceptions import LLMConnectionError, LLMResponseError


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

    @async_retry(max_attempts=3, base_delay=1.0, retryable_exceptions=(httpx.HTTPError,))
    async def chat(self, messages: list[dict], temperature: float = 0.1) -> str:
        client = await self._get_client()
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        response = await client.post(url, json=payload)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise LLMConnectionError(f"LLM 请求失败: {e.response.status_code} - {e.response.text}", self.provider_name)

        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise LLMResponseError(f"LLM 响应格式错误: {e}", self.provider_name, data)

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
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise LLMConnectionError(f"LLM 流式请求失败: {e.response.status_code}", self.provider_name)

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

    async def test_connection(self) -> dict:
        from ..exceptions import format_llm_result
        try:
            client = await self._get_client()
            url = f"{self.base_url}/chat/completions"
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Hello"}],
                "temperature": 0,
                "max_tokens": 1,
            }
            response = await client.post(url, json=payload, timeout=30.0)
            if response.status_code == 200:
                return format_llm_result(True, data={"message": "LLM 连接测试成功"})
            else:
                return format_llm_result(False, error=f"连接失败: {response.status_code}", provider=self.provider_name, code="HTTP_ERROR")
        except Exception as e:
            return format_llm_result(False, error=f"连接失败: {str(e)}", provider=self.provider_name, code="CONNECTION_ERROR")

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
