"""LLM 请求重试机制"""

import asyncio
import random
from functools import wraps
from typing import Callable, TypeVar, Any

T = TypeVar("T")


class RetryError(Exception):
    """重试耗尽后的异常"""
    def __init__(self, message: str, last_exception: Exception):
        super().__init__(message)
        self.last_exception = last_exception


def async_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple = (Exception,),
):
    """异步重试装饰器

    Args:
        max_attempts: 最大尝试次数
        base_delay: 基础延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        exponential_base: 指数退避基数
        jitter: 是否添加随机抖动
        retryable_exceptions: 可重试的异常类型元组
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        break

                    delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)

                    if jitter:
                        delay = delay * (0.5 + random.random() * 0.5)

                    await asyncio.sleep(delay)

            raise RetryError(
                f"重试 {max_attempts} 次后仍然失败: {last_exception}",
                last_exception
            )

        return wrapper
    return decorator


class RateLimiter:
    """简单的速率限制器"""

    def __init__(self, calls: int, period: float):
        self.calls = calls
        self.period = period
        self._tokens = calls
        self._last_update = asyncio.get_event_loop().time()

    async def acquire(self) -> None:
        loop = asyncio.get_event_loop()
        now = loop.time()

        elapsed = now - self._last_update
        self._tokens = min(self.calls, self._tokens + elapsed * (self.calls / self.period))
        self._last_update = now

        if self._tokens < 1:
            wait_time = (1 - self._tokens) * (self.period / self.calls)
            await asyncio.sleep(wait_time)
            self._tokens = 0
        else:
            self._tokens -= 1
