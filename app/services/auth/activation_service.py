"""用户激活 Token 服务。"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config.settings import settings
from app.models.activation_token import ActivationToken
from app.models.user import User
from app.services.auth.activation_repository import ActivationTokenRepository
from app.services.exceptions import ValidationError


class ActivationTokenService:
    """负责生成、刷新与消费激活 token。"""

    def __init__(self) -> None:
        self.repo = ActivationTokenRepository()
        self.expire_hours = getattr(settings, "activation_token_expire_hours", 48)

    def create_or_refresh(self, db: Session, *, user: User, purpose: str = "activation") -> ActivationToken:
        db.flush()
        token_value = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=self.expire_hours)
        activation = self.repo.get_by_user(db, user_id=user.id, purpose=purpose)
        if activation:
            activation.token = token_value
            activation.expires_at = expires_at
            activation.used_at = None
            activation.purpose = purpose
            db.add(activation)
        else:
            activation = ActivationToken(
                user_id=user.id,
                token=token_value,
                purpose=purpose,
                expires_at=expires_at,
            )
            db.add(activation)
        db.commit()
        db.refresh(activation)
        return activation

    def get_valid_token(self, db: Session, *, token: str, purpose: str = "activation") -> ActivationToken:
        record = self.repo.get_by_token(db, token=token, purpose=purpose)
        if not record:
            raise ValidationError("激活链接无效", code="activation_token_not_found")
        now = datetime.now(timezone.utc)
        if record.is_used():
            raise ValidationError("激活链接已使用", code="activation_token_used")
        if record.is_expired(now):
            raise ValidationError("激活链接已过期", code="activation_token_expired")
        return record

    def mark_used(self, db: Session, activation: ActivationToken) -> None:
        activation.used_at = datetime.now(timezone.utc)
        db.add(activation)

    def delete_for_user(self, db: Session, *, user: User, purpose: str = "activation") -> None:
        self.repo.delete_by_user(db, user_id=user.id, purpose=purpose)
        db.commit()
