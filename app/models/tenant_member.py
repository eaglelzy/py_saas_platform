"""租户成员模型，维护用户在租户中的角色与状态。"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum, auto

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class TenantMemberRole(StrEnum):
    """成员角色类型，映射到预置的 RBAC 规则。"""

    OWNER = auto()
    ADMIN = auto()
    MEMBER = auto()


class TenantMemberStatus(StrEnum):
    """成员在租户内的状态机。"""

    PENDING = auto()
    ACTIVE = auto()
    SUSPENDED = auto()
    REMOVED = auto()


class TenantMember(TimestampMixin, Base):
    """租户成员，绑定用户在租户内的角色、状态与审计信息。"""

    __tablename__ = "tenant_members"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_tenant_member"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="租户成员记录主键",
    )
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联租户 ID",
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联用户 ID",
    )
    role = Column(
        Enum(TenantMemberRole, name="tenant_member_role"),
        nullable=False,
        default=TenantMemberRole.MEMBER,
        comment="成员角色",
    )
    status = Column(
        Enum(TenantMemberStatus, name="tenant_member_status"),
        nullable=False,
        default=TenantMemberStatus.PENDING,
        comment="成员状态",
    )
    invited_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="邀请者用户 ID",
    )
    activated_at = Column(
        DateTime(timezone=True),
        comment="成员激活时间",
    )
    deactivated_at = Column(
        DateTime(timezone=True),
        comment="成员被停用或移除时间",
    )
    last_access_at = Column(
        DateTime(timezone=True),
        comment="最后一次访问时间",
    )
    notes = Column(Text, comment="运营或备注信息")

    tenant = relationship("Tenant", backref="members", lazy="joined")
    user = relationship("User", foreign_keys=[user_id], backref="tenant_memberships")
    inviter = relationship("User", foreign_keys=[invited_by_id])

    def __repr__(self) -> str:
        """简化调试输出。"""

        return (
            f"<TenantMember tenant={self.tenant_id} user={self.user_id} role={self.role}>"
        )
