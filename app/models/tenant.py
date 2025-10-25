"""租户模型定义，多租户租赁信息与状态管理。"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum, auto

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class TenantStatus(StrEnum):
    """租户在平台中的生命周期状态。"""

    PENDING = auto()
    ACTIVE = auto()
    SUSPENDED = auto()
    ARCHIVED = auto()


class PlanCode(StrEnum):
    """租户当前订阅套餐类型。"""

    FREE = auto()
    PRO = auto()


class Tenant(TimestampMixin, Base):
    """租户实体，记录企业基础信息、套餐与运营状态。"""

    __tablename__ = "tenants"
    __table_args__ = (
        UniqueConstraint("name", name="uq_tenants_name"),
        UniqueConstraint("slug", name="uq_tenants_slug"),
        CheckConstraint("member_limit > 0", name="ck_tenants_member_limit_positive"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="租户主键，UUID 确保全局唯一",
    )
    name = Column(String(200), nullable=False, comment="租户名称")
    slug = Column(String(120), nullable=False, comment="租户唯一标识，用于子域或路径")
    primary_owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="租户拥有者用户 ID",
    )
    status = Column(
        Enum(TenantStatus, name="tenant_status"),
        nullable=False,
        default=TenantStatus.PENDING,
        comment="租户当前状态",
    )
    plan_code = Column(
        Enum(PlanCode, name="tenant_plan_code"),
        nullable=False,
        default=PlanCode.FREE,
        comment="当前订阅套餐",
    )
    member_limit = Column(
        Integer,
        nullable=False,
        default=5,
        comment="成员数量上限，根据套餐设定",
    )
    contact_name = Column(String(120), nullable=False, comment="租户主要联系人姓名")
    contact_email = Column(String(320), nullable=False, comment="联系人邮箱")
    contact_phone = Column(String(32), nullable=False, comment="联系人电话")
    timezone = Column(
        String(64),
        nullable=False,
        default="Asia/Shanghai",
        comment="租户所在时区，用于通知与报表",
    )
    activated_at = Column(DateTime(timezone=True), comment="租户激活时间")
    deactivated_at = Column(DateTime(timezone=True), comment="租户停用时间")
    trial_ends_at = Column(DateTime(timezone=True), comment="试用结束时间")
    notes = Column(Text, comment="运营备注")

    owner = relationship("User", backref="owned_tenants", lazy="joined")

    def __repr__(self) -> str:
        """调试友好的显示格式。"""

        return f"<Tenant id={self.id} name={self.name} status={self.status}>"
