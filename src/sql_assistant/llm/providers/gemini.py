"""Google Gemini Provider"""

import httpx
from typing import AsyncGenerator, Optional

from ..base import BaseLLMProvider
from ..retry import async_retry
from ..exceptions import LLMConnectionError, LLMResponseError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API 实现"""

    def __init__(self, api_key: str, base_url: str, model: str):
        super().__init__(api_key, base_url, model)
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))
        return self._client

    def _convert_messages(self, messages: list[dict]) -> tuple[list[dict], Optional[str]]:
        """将 OpenAI 格式消息转为 Gemini 格式"""
        gemini_contents = []
        system_instruction = None

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_instruction = content
            elif role == "user":
                gemini_contents.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                gemini_contents.append({"role": "model", "parts": [{"text": content}]})

        return gemini_contents, system_instruction

    @async_retry(max_attempts=3, base_delay=1.0, retryable_exceptions=(httpx.HTTPError,))
    async def chat(self, messages: list[dict], temperature: float = 0.1) -> str:
        client = await self._get_client()
        contents, system_instruction = self._convert_messages(messages)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        params = {"key": self.api_key}

        payload = {
            "contents": contents,
            "generationConfig": {"temperature": temperature},
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        response = await client.post(url, params=params, json=payload)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise LLMConnectionError(f"Gemini 请求失败: {e.response.status_code} - {e.response.text}", "gemini")

        data = response.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise LLMResponseError(f"Gemini 响应格式错误: {e}", "gemini", data)

    async def chat_stream(self, messages: list[dict], temperature: float = 0.1) -> AsyncGenerator[str, None]:
        client = await self._get_client()
        contents, system_instruction = self._convert_messages(messages)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:streamGenerateContent"
        params = {"key": self.api_key, "alt": "sse"}

        payload = {
            "contents": contents,
            "generationConfig": {"temperature": temperature},
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        async with client.stream("POST", url, params=params, json=payload) as response:
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise LLMConnectionError(f"Gemini 流式请求失败: {e.response.status_code}", "gemini")

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        import json
                        data = json.loads(data_str)
                        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                        for part in parts:
                            text = part.get("text", "")
                            if text:
                                yield text
                    except Exception:
                        continue

    async def test_connection(self) -> dict:
        from ..exceptions import format_llm_result
        try:
            client = await self._get_client()
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            params = {"key": self.api_key}
            payload = {
                "contents": [{"role": "user", "parts": [{"text": "Hello"}]}],
                "generationConfig": {"temperature": 0, "maxOutputTokens": 1},
            }
            response = await client.post(url, params=params, json=payload, timeout=30.0)
            if response.status_code == 200:
                return format_llm_result(True, data={"message": "Gemini 连接测试成功"})
            else:
                return format_llm_result(False, error=f"连接失败: {response.status_code}", provider="gemini", code="HTTP_ERROR")
        except Exception as e:
            return format_llm_result(False, error=f"连接失败: {str(e)}", provider="gemini", code="CONNECTION_ERROR")

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
