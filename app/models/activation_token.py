"""用户激活 Token 模型。"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base, TimestampMixin


class ActivationToken(TimestampMixin, Base):
    """存储用户激活链接的随机 token。"""

    __tablename__ = "activation_tokens"
    __table_args__ = (
        UniqueConstraint("token", name="uq_activation_token_token"),
        UniqueConstraint("user_id", "purpose", name="uq_activation_user_purpose"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(128), nullable=False)
    purpose = Column(String(32), nullable=False, default="activation")
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True))

    def is_expired(self, now: datetime) -> bool:
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        return now >= expires_at

    def is_used(self) -> bool:
        return self.used_at is not None
