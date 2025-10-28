"""验证码生成与校验服务。"""

from __future__ import annotations

import json
import secrets
from typing import Any, Dict, Optional

from app.saas.core.config.settings import settings
from app.saas.core.redis import RedisClient, RedisKeys
from app.saas.services.exceptions import ValidationError


class VerificationService:
    """负责验证码生成、缓存、校验与失败次数统计。"""

    def __init__(self, client: Optional[RedisClient] = None) -> None:
        self.client = client or RedisClient()
        self.ttl_seconds = settings.verification_code_ttl_seconds
        self.max_attempts = settings.verification_code_max_attempts
        self.code_length = settings.verification_code_length

    def _random_code(self) -> str:
        """生成指定长度的数字验证码。"""

        alphabet = "0123456789"
        return "".join(secrets.choice(alphabet) for _ in range(self.code_length))

    def issue(
        self,
        *,
        scene: str,
        target: str,
        metadata: Optional[Dict[str, Any]] = None,
        custom_code: str | None = None,
        ttl_seconds: int | None = None,
    ) -> str:
        """生成或写入验证码，并返回最终验证码字符串。"""

        code = custom_code or self._random_code()
        payload = {"code": code, "meta": metadata or {}}
        key = RedisKeys.verification_code(scene, target)
        attempts_key = RedisKeys.verification_attempts(scene, target)

        ttl = ttl_seconds or self.ttl_seconds
        self.client.set(key, json.dumps(payload), expire_seconds=ttl)
        # 尝试次数独立计数，避免重复发送叠加旧值
        self.client.set(attempts_key, "0", expire_seconds=ttl)
        return code

    def validate(self, *, scene: str, target: str, code: str) -> None:
        """校验验证码，失败会记录尝试次数并抛出异常。"""

        key = RedisKeys.verification_code(scene, target)
        attempts_key = RedisKeys.verification_attempts(scene, target)

        data_raw = self.client.get(key)
        if not data_raw:
            raise ValidationError("验证码已失效或不存在", code="verification_code_expired")

        payload = json.loads(data_raw)
        expected_code = payload.get("code")

        if code != expected_code:
            attempts = int(self.client.incr(attempts_key))
            # 若是第一次 incr，需要设置过期时间，防止永不清理
            if attempts == 1:
                ttl = self.client.ttl(key)
                if ttl > 0:
                    self.client.expire(attempts_key, ttl)
            if attempts >= self.max_attempts:
                self.client.delete(key, attempts_key)
                raise ValidationError("验证码错误次数过多，请重新获取", code="verification_code_locked")
            raise ValidationError("验证码错误", code="verification_code_mismatch")

        # 校验成功后清理相关 key
        self.client.delete(key, attempts_key)


__all__ = ("VerificationService",)
