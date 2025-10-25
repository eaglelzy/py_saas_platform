"""订阅套餐与租户订阅相关 schema。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import Field

from app.models.subscription_plan import BillingCycle
from app.models.tenant_subscription import SubscriptionStatus
from app.schemas.common import IDMixin, ORMBaseModel, TimestampMixin


class SubscriptionPlanBase(ORMBaseModel):
    """订阅套餐公共字段。"""

    code: str = Field(min_length=2, max_length=50, description="套餐唯一代码")
    name: str = Field(min_length=2, max_length=100, description="套餐展示名称")
    description: Optional[str] = Field(default=None, description="套餐描述")
    member_limit: int = Field(ge=1, description="成员上限")
    api_quota_per_month: int = Field(ge=0, description="月度 API 调用配额，0 表示不限")
    price_cents: int = Field(ge=0, description="套餐价格（分）")
    currency: str = Field(min_length=3, max_length=8, default="CNY", description="货币编码")
    billing_cycle: BillingCycle = Field(description="计费周期")
    trial_days: int = Field(ge=0, description="试用天数")
    is_active: bool = Field(default=True, description="是否启用该套餐")
    features: Optional[dict[str, Any]] = Field(
        default=None,
        description="功能清单或配置，结构化数据",
    )


class SubscriptionPlanCreate(SubscriptionPlanBase):
    """创建套餐请求体。"""

    pass


class SubscriptionPlanUpdate(ORMBaseModel):
    """更新套餐请求体。"""

    name: Optional[str] = Field(default=None, min_length=2, max_length=100, description="套餐展示名称")
    description: Optional[str] = Field(default=None, description="套餐描述")
    member_limit: Optional[int] = Field(default=None, ge=1, description="成员上限")
    api_quota_per_month: Optional[int] = Field(default=None, ge=0, description="月度 API 配额")
    price_cents: Optional[int] = Field(default=None, ge=0, description="套餐价格（分）")
    currency: Optional[str] = Field(default=None, min_length=3, max_length=8, description="货币编码")
    billing_cycle: Optional[BillingCycle] = Field(default=None, description="计费周期")
    trial_days: Optional[int] = Field(default=None, ge=0, description="试用天数")
    is_active: Optional[bool] = Field(default=None, description="是否启用该套餐")
    features: Optional[dict[str, Any]] = Field(
        default=None,
        description="功能清单或配置，结构化数据",
    )


class SubscriptionPlanRead(IDMixin, SubscriptionPlanBase, TimestampMixin):
    """套餐对外输出。"""

    pass


class TenantSubscriptionCreate(ORMBaseModel):
    """创建租户订阅请求。"""

    tenant_id: str = Field(description="租户 ID")
    plan_id: Optional[str] = Field(default=None, description="套餐 ID")
    plan_code: str = Field(description="套餐代码")
    status: SubscriptionStatus = Field(default=SubscriptionStatus.TRIALING, description="订阅状态")
    starts_at: Optional[datetime] = Field(default=None, description="订阅开始时间")
    ends_at: Optional[datetime] = Field(default=None, description="订阅结束时间")
    trial_ends_at: Optional[datetime] = Field(default=None, description="试用结束时间")
    cancel_at: Optional[datetime] = Field(default=None, description="取消生效时间")
    cancel_at_period_end: bool = Field(default=False, description="是否在账期结束时取消")
    auto_renew: bool = Field(default=False, description="是否自动续费")
    member_limit: int = Field(ge=1, description="该订阅周期内的成员上限")
    price_cents: int = Field(ge=0, description="实际金额（分）")
    currency: str = Field(min_length=3, max_length=8, default="CNY", description="货币编码")
    activated_by_user_id: Optional[str] = Field(default=None, description="激活操作人 ID")
    notes: Optional[str] = Field(default=None, description="备注信息")


class TenantSubscriptionUpdate(ORMBaseModel):
    """更新租户订阅请求。"""

    status: Optional[SubscriptionStatus] = Field(default=None, description="订阅状态")
    ends_at: Optional[datetime] = Field(default=None, description="订阅结束时间")
    trial_ends_at: Optional[datetime] = Field(default=None, description="试用结束时间")
    cancel_at: Optional[datetime] = Field(default=None, description="取消生效时间")
    cancel_at_period_end: Optional[bool] = Field(default=None, description="是否在账期结束时取消")
    auto_renew: Optional[bool] = Field(default=None, description="是否自动续费")
    member_limit: Optional[int] = Field(default=None, ge=1, description="成员上限")
    price_cents: Optional[int] = Field(default=None, ge=0, description="实际金额（分）")
    currency: Optional[str] = Field(default=None, min_length=3, max_length=8, description="货币编码")
    cancelled_by_user_id: Optional[str] = Field(default=None, description="取消操作人 ID")
    notes: Optional[str] = Field(default=None, description="备注信息")


class TenantSubscriptionRead(IDMixin, ORMBaseModel, TimestampMixin):
    """租户订阅对外输出。"""

    tenant_id: str = Field(description="租户 ID")
    plan_id: Optional[str] = Field(default=None, description="套餐 ID")
    plan_code: str = Field(description="套餐代码")
    status: SubscriptionStatus = Field(description="订阅状态")
    starts_at: Optional[datetime] = Field(default=None, description="订阅开始时间")
    ends_at: Optional[datetime] = Field(default=None, description="订阅结束时间")
    trial_ends_at: Optional[datetime] = Field(default=None, description="试用结束时间")
    cancel_at: Optional[datetime] = Field(default=None, description="取消生效时间")
    cancel_at_period_end: bool = Field(description="是否在账期结束时取消")
    auto_renew: bool = Field(description="是否自动续费")
    member_limit: int = Field(description="订阅期间成员上限")
    price_cents: int = Field(description="实际金额（分）")
    currency: str = Field(description="货币编码")
    activated_by_user_id: Optional[str] = Field(default=None, description="激活操作人 ID")
    cancelled_by_user_id: Optional[str] = Field(default=None, description="取消操作人 ID")
    notes: Optional[str] = Field(default=None, description="备注信息")
