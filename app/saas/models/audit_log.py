"""审计日志持久化模型。"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Column, ForeignKey, String, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.saas.db.base import Base, TimestampMixin


class AuditAction(str):
    """常用审计事件名称。"""

    ACCOUNT_ACTIVATED = "account_activated"


class AuditLog(TimestampMixin, Base):
    """记录关键业务操作的审计日志。"""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL"))
    action = Column(String(120), nullable=False)
    payload = Column(JSON, nullable=True)
