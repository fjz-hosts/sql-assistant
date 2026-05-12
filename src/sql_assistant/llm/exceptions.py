"""LLM Provider 统一异常"""

from typing import Optional, Dict, Any


class LLMError(Exception):
    """LLM Provider 基础异常"""
    def __init__(self, message: str, provider: str = "", code: Optional[str] = None):
        super().__init__(message)
        self.provider = provider
        self.code = code

    def to_dict(self) -> dict:
        return {
            "success": False,
            "error": str(self),
            "provider": self.provider,
            "code": self.code,
        }


class LLMConnectionError(LLMError):
    """LLM 连接失败异常"""
    def __init__(self, message: str, provider: str = ""):
        super().__init__(message, provider, code="LLM_CONNECTION_FAILED")


class LLMTimeoutError(LLMError):
    """LLM 请求超时异常"""
    def __init__(self, message: str, provider: str = ""):
        super().__init__(message, provider, code="LLM_TIMEOUT")


class LLMAuthError(LLMError):
    """LLM 认证失败异常"""
    def __init__(self, message: str, provider: str = ""):
        super().__init__(message, provider, code="LLM_AUTH_FAILED")


class LLMRateLimitError(LLMError):
    """LLM 限流异常"""
    def __init__(self, message: str, provider: str = "", retry_after: Optional[int] = None):
        super().__init__(message, provider, code="LLM_RATE_LIMITED")
        self.retry_after = retry_after

    def to_dict(self) -> dict:
        result = super().to_dict()
        if self.retry_after:
            result["retry_after"] = self.retry_after
        return result


class LLMResponseError(LLMError):
    """LLM 响应解析异常"""
    def __init__(self, message: str, provider: str = "", raw_response: Any = None):
        super().__init__(message, provider, code="LLM_RESPONSE_ERROR")
        self.raw_response = raw_response

    def to_dict(self) -> dict:
        result = super().to_dict()
        if self.raw_response:
            result["raw_response"] = str(self.raw_response)[:500]
        return result


def format_llm_result(
    success: bool,
    data: Any = None,
    error: Optional[str] = None,
    provider: str = "",
    code: Optional[str] = None,
) -> Dict[str, Any]:
    """统一格式化 LLM 返回结果

    Args:
        success: 是否成功
        data: 成功时返回的数据
        error: 失败时的错误信息
        provider: 提供商名称
        code: 错误码

    Returns:
        统一格式的字典
    """
    result: Dict[str, Any] = {"success": success}

    if success:
        result["data"] = data
    else:
        result["error"] = error or "未知错误"
        if code:
            result["code"] = code
        if provider:
            result["provider"] = provider

    return result
