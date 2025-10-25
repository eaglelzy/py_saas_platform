"""租户订阅记录模型，追踪套餐生效周期。"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum, auto

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class SubscriptionStatus(StrEnum):
    """租户订阅状态枚举。"""

    TRIALING = auto()
    ACTIVE = auto()
    PAST_DUE = auto()
    CANCELLED = auto()
    EXPIRED = auto()


class TenantSubscription(TimestampMixin, Base):
    """租户订阅记录，描述套餐生效区间与计费信息。"""

    __tablename__ = "tenant_subscriptions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="订阅记录主键",
    )
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联租户 ID",
    )
    plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subscription_plans.id", ondelete="SET NULL"),
        comment="关联订阅套餐 ID",
    )
    plan_code = Column(
        String(50),
        nullable=False,
        comment="订阅套餐代码（冗余存储）",
    )
    status = Column(
        Enum(SubscriptionStatus, name="tenant_subscription_status"),
        nullable=False,
        default=SubscriptionStatus.TRIALING,
        comment="当前订阅状态",
    )
    starts_at = Column(
        DateTime(timezone=True),
        comment="订阅开始时间",
    )
    ends_at = Column(
        DateTime(timezone=True),
        comment="订阅结束时间",
    )
    trial_ends_at = Column(
        DateTime(timezone=True),
        comment="试用结束时间",
    )
    cancel_at = Column(
        DateTime(timezone=True),
        comment="取消生效时间",
    )
    cancel_at_period_end = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否在当前账期结束时取消",
    )
    auto_renew = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否开启自动续费",
    )
    member_limit = Column(
        Integer,
        nullable=False,
        comment="该周期的成员上限",
    )
    price_cents = Column(
        Integer,
        nullable=False,
        default=0,
        comment="实际金额（分）",
    )
    currency = Column(
        String(8),
        nullable=False,
        default="CNY",
        comment="结算币种",
    )
    activated_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="激活操作人",
    )
    cancelled_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="取消操作人",
    )
    notes = Column(
        Text,
        comment="备注信息",
    )

    tenant = relationship("Tenant", backref="subscriptions")
    plan = relationship("SubscriptionPlan", backref="tenant_subscriptions")
    activated_by = relationship("User", foreign_keys=[activated_by_user_id])
    cancelled_by = relationship("User", foreign_keys=[cancelled_by_user_id])

    def __repr__(self) -> str:
        """简洁调试输出。"""

        return f"<TenantSubscription tenant={self.tenant_id} plan={self.plan_code} status={self.status}>"
