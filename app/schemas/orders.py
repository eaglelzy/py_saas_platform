"""订阅订单相关 schema。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.models.subscription_order import SubscriptionOrderStatus
from app.schemas.common import IDMixin, ORMBaseModel, TimestampMixin


class SubscriptionOrderCreate(ORMBaseModel):
    """提交订阅订单请求体。"""

    tenant_id: str = Field(description="租户 ID")
    requested_by_user_id: str = Field(description="申请人用户 ID")
    current_plan_id: Optional[str] = Field(default=None, description="当前套餐 ID")
    target_plan_id: Optional[str] = Field(default=None, description="目标套餐 ID")
    current_plan_code: str = Field(description="当前套餐代码")
    target_plan_code: str = Field(description="目标套餐代码")
    amount_cents: int = Field(ge=0, description="应付金额（分）")
    currency: str = Field(min_length=3, max_length=8, default="CNY", description="货币编码")
    notes: Optional[str] = Field(default=None, description="备注信息")
    extra_metadata: Optional[dict[str, str]] = Field(
        default=None,
        description="附加信息，如对账数据、附件引用",
    )


class SubscriptionOrderProcess(ORMBaseModel):
    """平台管理员处理订单请求体。"""

    status: SubscriptionOrderStatus = Field(description="订单处理后的状态")
    processed_by_user_id: str = Field(description="处理人用户 ID")
    payment_reference: Optional[str] = Field(default=None, description="线下支付凭证号")
    processed_at: Optional[datetime] = Field(default=None, description="处理时间")
    paid_at: Optional[datetime] = Field(default=None, description="支付确认时间")
    expires_at: Optional[datetime] = Field(default=None, description="订阅到期时间")
    notes: Optional[str] = Field(default=None, description="运营备注")


class SubscriptionOrderRead(IDMixin, ORMBaseModel, TimestampMixin):
    """订阅订单对外输出。"""

    tenant_id: str = Field(description="租户 ID")
    requested_by_user_id: Optional[str] = Field(default=None, description="申请人用户 ID")
    processed_by_user_id: Optional[str] = Field(default=None, description="处理人用户 ID")
    current_plan_id: Optional[str] = Field(default=None, description="当前套餐 ID")
    target_plan_id: Optional[str] = Field(default=None, description="目标套餐 ID")
    current_plan_code: str = Field(description="当前套餐代码")
    target_plan_code: str = Field(description="目标套餐代码")
    status: SubscriptionOrderStatus = Field(description="订单状态")
    amount_cents: int = Field(description="金额（分）")
    currency: str = Field(description="货币编码")
    payment_reference: Optional[str] = Field(default=None, description="线下支付凭证")
    processed_at: Optional[datetime] = Field(default=None, description="处理时间")
    paid_at: Optional[datetime] = Field(default=None, description="支付确认时间")
    expires_at: Optional[datetime] = Field(default=None, description="订阅到期时间")
    notes: Optional[str] = Field(default=None, description="备注信息")
    extra_metadata: Optional[dict[str, str]] = Field(default=None, description="附加信息")


class SubscriptionOrderSummary(IDMixin, ORMBaseModel):
    """订单列表展示结构。"""

    tenant_id: str = Field(description="租户 ID")
    status: SubscriptionOrderStatus = Field(description="订单状态")
    target_plan_code: str = Field(description="目标套餐代码")
    amount_cents: int = Field(description="金额（分）")
