"""JWT 生成工具。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from app.core.config.settings import settings
from jwt import encode, decode


def _build_payload(subject: str, expires_delta: timedelta, token_type: str, extra: Dict[str, Any] | None = None) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + expires_delta,
        "type": token_type,
    }
    if extra:
        payload.update(extra)
    return payload


def create_access_token(subject: str, *, extra: Dict[str, Any] | None = None) -> str:
    """生成 Access Token。"""

    expires = timedelta(minutes=settings.access_token_expire_minutes)
    payload = _build_payload(subject, expires, "access", extra)
    return encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str, *, extra: Dict[str, Any] | None = None) -> str:
    """生成 Refresh Token。"""

    expires = timedelta(days=settings.refresh_token_expire_days)
    payload = _build_payload(subject, expires, "refresh", extra)
    return encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """解析 JWT，返回 payload。"""

    return decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


__all__ = ("create_access_token", "create_refresh_token", "decode_token")
