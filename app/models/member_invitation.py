"""租户成员邀请模型，追踪邀请流程与状态。"""

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
from app.models.tenant_member import TenantMemberRole


class InvitationStatus(StrEnum):
    """邀请状态枚举。"""

    PENDING = auto()
    ACCEPTED = auto()
    REVOKED = auto()
    EXPIRED = auto()


class MemberInvitation(TimestampMixin, Base):
    """租户成员邀请记录，记录邀请生命周期与元数据。"""

    __tablename__ = "member_invitations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_member_invitation_email"),
        UniqueConstraint("token", name="uq_member_invitation_token"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="邀请记录主键",
    )
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        comment="目标租户 ID",
    )
    invited_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="邀请发起者用户 ID",
    )
    role = Column(
        Enum(TenantMemberRole, name="member_invitation_role"),
        nullable=False,
        default=TenantMemberRole.MEMBER,
        comment="邀请预设角色",
    )
    email = Column(String(320), nullable=False, comment="受邀成员邮箱")
    token = Column(String(128), nullable=False, comment="邀请校验 Token")
    status = Column(
        Enum(InvitationStatus, name="member_invitation_status"),
        nullable=False,
        default=InvitationStatus.PENDING,
        comment="邀请当前状态",
    )
    expires_at = Column(DateTime(timezone=True), comment="邀请过期时间")
    accepted_at = Column(DateTime(timezone=True), comment="邀请被接受时间")
    revoked_at = Column(DateTime(timezone=True), comment="邀请被撤销时间")
    message = Column(Text, comment="附言或备注")

    tenant = relationship("Tenant", backref="invitations", lazy="joined")
    inviter = relationship("User", foreign_keys=[invited_by_id])

    def __repr__(self) -> str:
        """简化调试输出。"""

        return f"<MemberInvitation tenant={self.tenant_id} email={self.email} status={self.status}>"
