"""Refresh Token 管理服务。"""

from __future__ import annotations

import base64
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config.settings import settings
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.exceptions import ValidationError


class RefreshTokenService:
    """负责刷新 Token 的生成、验证、撤销。"""

    def __init__(self) -> None:
        self.expire_days = getattr(settings, "refresh_token_expire_days", settings.refresh_token_expire_days)

    def _hash_token(self, token: str) -> str:
        return base64.urlsafe_b64encode(token.encode("utf-8")).decode("utf-8")

    def issue(self, db: Session, *, user: User, user_agent: str | None = None, ip_address: str | None = None) -> str:
        token = secrets.token_urlsafe(48)
        token_hash = self._hash_token(token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.expire_days)
        record = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        db.add(record)
        db.commit()
        return token

    def verify(self, db: Session, token: str) -> RefreshToken:
        token_hash = self._hash_token(token)
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        record = db.execute(stmt).scalars().first()
        if not record:
            raise ValidationError("刷新令牌无效", code="refresh_token_invalid")
        now = datetime.now(timezone.utc)
        if record.is_revoked():
            raise ValidationError("刷新令牌已撤销", code="refresh_token_revoked")
        if record.is_expired(now):
            raise ValidationError("刷新令牌已过期", code="refresh_token_expired")
        return record

    def revoke(self, db: Session, token: str) -> None:
        try:
            record = self.verify(db, token)
        except ValidationError:
            # 已失效，无需撤销
            return
        record.revoked_at = datetime.now(timezone.utc)
        db.add(record)
        db.commit()

    def revoke_user_tokens(self, db: Session, user: User) -> None:
        stmt = select(RefreshToken).where(RefreshToken.user_id == user.id)
        now = datetime.now(timezone.utc)
        for record in db.execute(stmt).scalars().all():
            record.revoked_at = now
            db.add(record)
        db.commit()
