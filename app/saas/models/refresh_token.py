"""刷新 Token 模型定义。"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.saas.db.base import Base, TimestampMixin


class RefreshToken(TimestampMixin, Base):
    """存储用户刷新 Token（哈希存储）。"""

    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True))
    user_agent = Column(String(255))
    ip_address = Column(String(64))

    def is_expired(self, now: datetime) -> bool:
        return now >= self.expires_at

    def is_revoked(self) -> bool:
        return self.revoked_at is not None
