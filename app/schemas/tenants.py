"""租户相关的请求与响应 Schema 定义。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import EmailStr, Field, field_validator

from app.models.tenant import PlanCode, TenantStatus
from app.schemas.common import IDMixin, ORMBaseModel, TimestampMixin
from app.utils import validate_phone, validate_slug


class TenantBase(ORMBaseModel):
    """租户公共字段。"""

    name: str = Field(min_length=2, max_length=200, description="租户名称")
    slug: str = Field(min_length=2, max_length=120, description="租户唯一标识")
    contact_name: str = Field(min_length=1, max_length=120, description="联系人姓名")
    contact_email: EmailStr = Field(description="联系人邮箱")
    contact_phone: str = Field(min_length=5, max_length=32, description="联系人电话")
    timezone: str = Field(default="Asia/Shanghai", max_length=64, description="租户所在时区")
    notes: Optional[str] = Field(default=None, description="运营备注")

    @field_validator("slug")
    @classmethod
    def validate_slug_format(cls, value: str) -> str:
        return validate_slug(value)

    @field_validator("contact_phone")
    @classmethod
    def validate_phone_format(cls, value: str) -> str:
        return validate_phone(value)


class TenantCreate(TenantBase):
    """创建租户时使用的字段。"""

    primary_owner_id: str = Field(description="租户拥有者用户 ID")
    plan_code: PlanCode = Field(default=PlanCode.FREE, description="初始套餐代码")
    member_limit: int = Field(default=5, ge=1, description="初始成员上限")


class TenantUpdate(ORMBaseModel):
    """更新租户信息。"""

    name: Optional[str] = Field(default=None, min_length=2, max_length=200, description="租户名称")
    contact_name: Optional[str] = Field(default=None, min_length=1, max_length=120, description="联系人姓名")
    contact_email: Optional[EmailStr] = Field(default=None, description="联系人邮箱")
    contact_phone: Optional[str] = Field(default=None, min_length=5, max_length=32, description="联系人电话")
    timezone: Optional[str] = Field(default=None, max_length=64, description="租户所在时区")
    notes: Optional[str] = Field(default=None, description="运营备注")
    member_limit: Optional[int] = Field(default=None, ge=1, description="成员上限")


class TenantStatusUpdate(ORMBaseModel):
    """更新租户状态请求体。"""

    status: TenantStatus = Field(description="目标租户状态")


class TenantPlanUpdate(ORMBaseModel):
    """调整租户套餐。"""

    plan_code: PlanCode = Field(description="目标套餐代码")
    member_limit: Optional[int] = Field(default=None, ge=1, description="新的成员上限，如未提供将按套餐默认值更新")
    activated_at: Optional[datetime] = Field(default=None, description="套餐切换生效时间")
    expires_at: Optional[datetime] = Field(default=None, description="套餐到期时间")


class TenantRead(IDMixin, TenantBase, TimestampMixin):
    """租户对外输出字段。"""

    status: TenantStatus = Field(
        description="租户状态",
        json_schema_extra={"example": TenantStatus.ACTIVE.value},
    )
    plan_code: PlanCode = Field(
        description="当前套餐代码",
        json_schema_extra={"example": PlanCode.PRO.value},
    )
    member_limit: int = Field(description="成员上限", json_schema_extra={"example": 10})
    activated_at: Optional[datetime] = Field(
        default=None,
        description="租户激活时间",
        json_schema_extra={"example": "2025-01-10T02:00:00+00:00"},
    )
    deactivated_at: Optional[datetime] = Field(
        default=None,
        description="租户停用时间",
        json_schema_extra={"example": None},
    )
    trial_ends_at: Optional[datetime] = Field(
        default=None,
        description="试用结束时间",
        json_schema_extra={"example": "2025-01-17T02:00:00+00:00"},
    )


class TenantSummary(IDMixin, ORMBaseModel):
    """租户摘要信息，适合列表展示。"""

    name: str = Field(description="租户名称")
    status: TenantStatus = Field(description="租户状态")
    plan_code: PlanCode = Field(description="当前套餐代码")
    member_limit: int = Field(description="成员上限")
