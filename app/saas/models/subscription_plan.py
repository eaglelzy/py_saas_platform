"""订阅套餐配置模型。"""

from __future__ import annotations

import uuid
from enum import StrEnum, auto

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Enum,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from app.saas.db.base import Base, TimestampMixin


class BillingCycle(StrEnum):
    """订阅计费周期。"""

    MONTHLY = auto()
    YEARLY = auto()
    LIFETIME = auto()


class SubscriptionPlan(TimestampMixin, Base):
    """订阅套餐配置，用于驱动租户订阅策略。"""

    __tablename__ = "subscription_plans"
    __table_args__ = (
        UniqueConstraint("code", name="uq_subscription_plan_code"),
        CheckConstraint("member_limit > 0", name="ck_subscription_plan_member_limit_positive"),
        CheckConstraint("price_cents >= 0", name="ck_subscription_plan_price_non_negative"),
        CheckConstraint("api_quota_per_month >= 0", name="ck_subscription_plan_quota_non_negative"),
        CheckConstraint("trial_days >= 0", name="ck_subscription_plan_trial_days_non_negative"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="套餐主键",
    )
    code = Column(
        String(50),
        nullable=False,
        comment="套餐唯一代码",
    )
    name = Column(
        String(100),
        nullable=False,
        comment="套餐展示名称",
    )
    description = Column(
        Text,
        comment="套餐描述",
    )
    member_limit = Column(
        Integer,
        nullable=False,
        default=5,
        comment="成员上限",
    )
    api_quota_per_month = Column(
        Integer,
        nullable=False,
        default=0,
        comment="月度 API 调用配额，0 表示不限",
    )
    price_cents = Column(
        Integer,
        nullable=False,
        default=0,
        comment="套餐价格（分）",
    )
    currency = Column(
        String(8),
        nullable=False,
        default="CNY",
        comment="货币编码",
    )
    billing_cycle = Column(
        Enum(BillingCycle, name="subscription_plan_billing_cycle"),
        nullable=False,
        default=BillingCycle.MONTHLY,
        comment="计费周期",
    )
    trial_days = Column(
        Integer,
        nullable=False,
        default=0,
        comment="试用天数",
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否启用该套餐",
    )
    features = Column(
        JSON,
        comment="套餐功能点描述（结构化数据）",
    )

    def __repr__(self) -> str:
        """简洁调试输出。"""

        return f"<SubscriptionPlan code={self.code} name={self.name}>"
