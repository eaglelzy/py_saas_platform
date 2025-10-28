"""基于 Redis 的令牌黑名单与会话管理。"""

from __future__ import annotations

from datetime import timedelta
from typing import Optional

from app.saas.core.config.settings import settings
from app.saas.core.redis import RedisClient, RedisKeys


class TokenBlacklistService:
    """负责访问令牌黑名单与刷新会话的存储。"""

    def __init__(self, client: Optional[RedisClient] = None) -> None:
        self.client = client or RedisClient()
        self.access_token_ttl = settings.access_token_expire_minutes * 60
        self.refresh_token_ttl = settings.refresh_token_expire_days * 24 * 60 * 60

    def block_access_token(self, jti: str, *, ttl_seconds: int | None = None) -> None:
        """将访问令牌标记为失效。"""

        ttl = ttl_seconds or self.access_token_ttl
        key = RedisKeys.jwt_blacklist(jti)
        self.client.set(key, "1", expire_seconds=ttl)

    def is_access_token_blocked(self, jti: str) -> bool:
        """判断访问令牌是否已进入黑名单。"""

        key = RedisKeys.jwt_blacklist(jti)
        value = self.client.get(key)
        return value is not None

    def bind_refresh_session(self, user_id: str, token_id: str, *, ttl_seconds: int | None = None) -> None:
        """记录用户当前有效的刷新令牌 ID，用于强制单会话登录。"""

        ttl = ttl_seconds or self.refresh_token_ttl
        key = RedisKeys.refresh_session(user_id)
        self.client.set(key, token_id, expire_seconds=ttl)

    def get_refresh_session(self, user_id: str) -> str | None:
        """读取用户已登记的刷新令牌 ID。"""

        key = RedisKeys.refresh_session(user_id)
        value = self.client.get(key)
        return str(value) if value else None

    def revoke_refresh_session(self, user_id: str) -> None:
        """撤销用户记录的刷新令牌会话。"""

        key = RedisKeys.refresh_session(user_id)
        self.client.delete(key)


__all__ = ("TokenBlacklistService",)
