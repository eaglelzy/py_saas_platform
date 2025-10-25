"""租户订阅订单模型，记录升级/续费申请与线下支付状态。"""

from __future__ import annotations

import uuid
from enum import StrEnum, auto

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class SubscriptionOrderStatus(StrEnum):
    """订阅订单处理状态。"""

    PENDING = auto()
    APPROVED = auto()
    REJECTED = auto()
    PAID = auto()
    CANCELLED = auto()


class SubscriptionOrder(TimestampMixin, Base):
    """租户订阅订单记录，覆盖升级/续费申请到支付确认。"""

    __tablename__ = "subscription_orders"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="订单主键",
    )
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联租户 ID",
    )
    requested_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="订单申请人（租户管理员）",
    )
    processed_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="订单处理人（平台管理员）",
    )
    current_plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subscription_plans.id", ondelete="SET NULL"),
        comment="当前套餐 ID",
    )
    target_plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subscription_plans.id", ondelete="SET NULL"),
        comment="目标套餐 ID",
    )
    current_plan_code = Column(
        String(50),
        nullable=False,
        comment="当前套餐代码（冗余）",
    )
    target_plan_code = Column(
        String(50),
        nullable=False,
        comment="目标套餐代码（冗余）",
    )
    status = Column(
        Enum(SubscriptionOrderStatus, name="subscription_order_status"),
        nullable=False,
        default=SubscriptionOrderStatus.PENDING,
        comment="订单状态",
    )
    amount_cents = Column(
        Integer,
        nullable=False,
        default=0,
        comment="应付金额（分）",
    )
    currency = Column(
        String(8),
        nullable=False,
        default="CNY",
        comment="货币编码",
    )
    payment_reference = Column(
        String(120),
        comment="线下支付凭证号/备注",
    )
    processed_at = Column(
        DateTime(timezone=True),
        comment="订单处理时间",
    )
    paid_at = Column(
        DateTime(timezone=True),
        comment="支付确认时间",
    )
    expires_at = Column(
        DateTime(timezone=True),
        comment="本次订阅到期时间",
    )
    notes = Column(
        Text,
        comment="运营备注",
    )
    extra_metadata = Column(
        JSON,
        comment="附加信息（对账、附件等）",
    )

    tenant = relationship("Tenant", backref="subscription_orders")
    requester = relationship("User", foreign_keys=[requested_by_user_id])
    processor = relationship("User", foreign_keys=[processed_by_user_id])
    current_plan = relationship(
        "SubscriptionPlan", foreign_keys=[current_plan_id], backref="orders_current"
    )
    target_plan = relationship(
        "SubscriptionPlan", foreign_keys=[target_plan_id], backref="orders_target"
    )

    def __repr__(self) -> str:
        """简洁调试输出。"""

        return (
            f"<SubscriptionOrder tenant={self.tenant_id} "
            f"{self.current_plan_code}->{self.target_plan_code} status={self.status}>"
        )
