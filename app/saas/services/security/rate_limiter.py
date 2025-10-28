"""Redis 限流服务，实现固定窗口计数。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.saas.core.config.settings import settings
from app.saas.core.redis import RedisClient, RedisKeys
from app.saas.services.exceptions import RateLimitExceededError


@dataclass(frozen=True)
class RateLimitResult:
    """限流结果载体，用于返回剩余次数与窗口信息。"""

    remaining: int
    limit: int
    window_seconds: int
    retry_after: int


class RateLimiterService:
    """使用 Redis 计数器实现固定窗口限流。"""

    def __init__(self, client: Optional[RedisClient] = None) -> None:
        self.client = client or RedisClient()
        self.default_limit = settings.rate_limit_per_minute
        self.default_window = settings.rate_limit_default_window_seconds

    def _build_key(self, scope: str, identifier: str, window_seconds: int) -> str:
        return RedisKeys.rate_limit(scope, identifier, f"{window_seconds}s")

    def check(
        self,
        *,
        scope: str,
        identifier: str,
        limit: int | None = None,
        window_seconds: int | None = None,
    ) -> RateLimitResult:
        """累计请求计数，并在超限时抛出异常。"""

        threshold = limit or self.default_limit
        window = window_seconds or self.default_window
        key = self._build_key(scope, identifier, window)

        current = self.client.incr(key)
        if current == 1:
            self.client.expire(key, window)

        if current > threshold:
            ttl = self.client.ttl(key)
            retry_after = ttl if ttl > 0 else window
            raise RateLimitExceededError(
                "请求过于频繁，请稍后再试",
                code="rate_limit_exceeded",
                context={"retry_after": retry_after},
            )

        remaining = max(threshold - current, 0)
        ttl = self.client.ttl(key)
        retry_after = ttl if ttl > 0 else window
        return RateLimitResult(
            remaining=remaining,
            limit=threshold,
            window_seconds=window,
            retry_after=retry_after,
        )


__all__ = ("RateLimiterService", "RateLimitResult")
