"""租户入驻申请模型，记录企业提交与审核流程。"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum, auto

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class ApplicationStatus(StrEnum):
    """租户入驻申请的审核状态。"""

    PENDING = auto()
    APPROVED = auto()
    REJECTED = auto()
    CANCELLED = auto()

class ReviewStatus(StrEnum):
    """审核状态枚举，仅用于审核操作。"""
    APPROVED = auto()
    REJECTED = auto()

class TenantApplication(TimestampMixin, Base):
    """租户入驻申请，覆盖提交与审核全流程。"""

    __tablename__ = "tenant_applications"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="申请记录主键",
    )
    company_name = Column(
        String(200),
        nullable=False,
        comment="申请企业名称",
    )
    contact_name = Column(
        String(120),
        nullable=False,
        comment="联系人姓名",
    )
    contact_email = Column(
        String(320),
        nullable=False,
        comment="联系人邮箱",
    )
    contact_phone = Column(
        String(32),
        nullable=False,
        comment="联系人电话",
    )
    business_description = Column(
        Text,
        comment="业务简介或申请说明",
    )
    attachments = Column(
        JSON,
        comment="附件信息（例如证照、截图的链接）",
    )
    submitted_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="提交人用户 ID（如已注册）",
    )
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="SET NULL"),
        comment="对应创建的租户 ID（审核通过后填入）",
    )
    status = Column(
        Enum(ApplicationStatus, name="tenant_application_status"),
        nullable=False,
        default=ApplicationStatus.PENDING,
        comment="申请当前状态",
    )
    reviewed_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="平台审核人用户 ID",
    )
    reviewed_at = Column(
        DateTime(timezone=True),
        comment="审核时间",
    )
    rejection_reason = Column(
        Text,
        comment="驳回原因",
    )
    notes = Column(
        Text,
        comment="运营备注",
    )

    submitter = relationship("User", foreign_keys=[submitted_by_user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by_user_id])
    tenant = relationship("Tenant", backref="applications")

    def __repr__(self) -> str:
        """简洁的调试输出。"""

        return f"<TenantApplication id={self.id} status={self.status}>"
