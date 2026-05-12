"""Anthropic Claude Provider"""

import httpx
from typing import AsyncGenerator, Optional

from ..base import BaseLLMProvider
from ..retry import async_retry
from ..exceptions import LLMConnectionError, LLMResponseError


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

    @async_retry(max_attempts=3, base_delay=1.0, retryable_exceptions=(httpx.HTTPError,))
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
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise LLMConnectionError(f"Claude 请求失败: {e.response.status_code} - {e.response.text}", "claude")

        data = response.json()
        try:
            return data["content"][0]["text"]
        except (KeyError, IndexError) as e:
            raise LLMResponseError(f"Claude 响应格式错误: {e}", "claude", data)

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
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise LLMConnectionError(f"Claude 流式请求失败: {e.response.status_code}", "claude")

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

    async def test_connection(self) -> dict:
        from ..exceptions import format_llm_result
        try:
            client = await self._get_client()
            url = "https://api.anthropic.com/v1/messages"
            payload = {
                "model": self.model,
                "max_tokens": 1,
                "temperature": 0,
                "messages": [{"role": "user", "content": "Hello"}],
            }
            response = await client.post(url, json=payload, timeout=30.0)
            if response.status_code == 200:
                return format_llm_result(True, data={"message": "Claude 连接测试成功"})
            else:
                return format_llm_result(False, error=f"连接失败: {response.status_code}", provider="claude", code="HTTP_ERROR")
        except Exception as e:
            return format_llm_result(False, error=f"连接失败: {str(e)}", provider="claude", code="CONNECTION_ERROR")

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
