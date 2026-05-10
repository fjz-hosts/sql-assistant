"""Google Gemini Provider"""

import httpx
from typing import AsyncGenerator, Optional

from ..base import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API 实现"""

    def __init__(self, api_key: str, base_url: str, model: str):
        super().__init__(api_key, base_url, model)
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))
        return self._client

    def _convert_messages(self, messages: list[dict]) -> list[dict]:
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
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

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
            response.raise_for_status()
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

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
