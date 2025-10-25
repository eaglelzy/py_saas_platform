"""用户相关 schema。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import EmailStr, Field, field_validator

from app.schemas.common import IDMixin, ORMBaseModel, TimestampMixin
from app.utils import validate_password, validate_phone


class UserBase(ORMBaseModel):
    """用户公共字段。"""

    email: EmailStr = Field(description="用户邮箱")
    display_name: Optional[str] = Field(default=None, max_length=150, description="展示名称")
    full_name: Optional[str] = Field(default=None, max_length=150, description="真实姓名")
    phone_number: Optional[str] = Field(default=None, max_length=32, description="手机号")
    avatar_url: Optional[str] = Field(default=None, max_length=1024, description="头像地址")
    timezone: str = Field(default="UTC", max_length=64, description="时区信息")

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return validate_phone(value)


class UserCreate(ORMBaseModel):
    """创建用户。"""

    email: EmailStr = Field(description="用户邮箱")
    password: str = Field(min_length=8, description="登录密码")
    display_name: Optional[str] = Field(default=None, max_length=150, description="展示名称")
    full_name: Optional[str] = Field(default=None, max_length=150, description="真实姓名")
    phone_number: Optional[str] = Field(default=None, max_length=32, description="手机号")
    avatar_url: Optional[str] = Field(default=None, max_length=1024, description="头像地址")
    timezone: str = Field(default="UTC", max_length=64, description="时区信息")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        return validate_password(value)


class UserUpdate(ORMBaseModel):
    """更新用户资料。"""

    display_name: Optional[str] = Field(default=None, max_length=150, description="展示名称")
    full_name: Optional[str] = Field(default=None, max_length=150, description="真实姓名")
    phone_number: Optional[str] = Field(default=None, max_length=32, description="手机号")
    avatar_url: Optional[str] = Field(default=None, max_length=1024, description="头像地址")
    timezone: Optional[str] = Field(default=None, max_length=64, description="时区信息")


class UserRead(IDMixin, UserBase, TimestampMixin):
    """用户对外输出。"""

    is_active: bool = Field(description="是否激活")
    is_superuser: bool = Field(description="是否平台管理员")
    is_locked: bool = Field(description="是否已锁定")
    last_login_at: Optional[datetime] = Field(default=None, description="最近登录时间")


class CurrentUser(UserRead):
    """带租户上下文的当前用户。"""

    active_tenant_id: Optional[str] = Field(default=None, description="当前租户 ID")
    tenant_ids: list[str] = Field(default_factory=list, description="可访问的租户 ID 列表")
