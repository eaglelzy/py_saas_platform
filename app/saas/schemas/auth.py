"""认证与授权相关 schema。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.saas.schemas.common import ORMBaseModel
from app.saas.utils import validate_password, validate_phone, validate_slug
from app.saas.schemas.users import UserRead


class AuthLoginRequest(BaseModel):
    """登录请求体。"""

    email: EmailStr = Field(description="登录邮箱")
    password: str = Field(min_length=8, description="登录密码")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> EmailStr:
        return str(value).lower()

class VerifyRegisterRequest(BaseModel):
    """发送注册验证码请求体。"""

    email: EmailStr = Field(description="登录邮箱")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> EmailStr:
        return str(value).lower()


class ConsultantRegisterRequest(BaseModel):
    """顾问注册请求体。"""

    email: EmailStr = Field(description="登录邮箱")
    password: str = Field(min_length=8, description="登录密码")
    verification_code: str = Field(min_length=4, max_length=10, description="验证码")
    full_name: Optional[str] = Field(default=None, max_length=150, description="真实姓名")
    display_name: Optional[str] = Field(default=None, max_length=150, description="展示名称")
    workspace_name: Optional[str] = Field(default=None, max_length=200, description="工作室或企业名称")
    phone_number: Optional[str] = Field(default=None, max_length=32, description="联系电话")
    service_country: Optional[str] = Field(default=None, max_length=120, description="主要服务国家或地区")
    experience_years: Optional[int] = Field(default=None, ge=0, le=60, description="从业年限")
    # timezone: Optional[str] = Field(default="Asia/Shanghai", max_length=64, description="所在时区")
    # slug: Optional[str] = Field(default=None, max_length=120, description="租户自定义标识（可选）")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> EmailStr:
        return str(value).lower()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        return validate_password(value)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_optional(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return validate_phone(value)

    # @field_validator("slug")
    # @classmethod
    # def normalize_slug(cls, value: Optional[str]) -> Optional[str]:
    #     if value is None:
    #         return value
    #     return validate_slug(value)


class AuthTokenPair(BaseModel):
    """登录成功后返回的 Token 数据。"""

    access_token: str = Field(description="访问令牌")
    refresh_token: str = Field(description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(description="访问令牌有效期（秒）")


class TokenRefreshRequest(BaseModel):
    """刷新 Token 请求体。"""

    refresh_token: str = Field(description="刷新令牌")


class LogoutRequest(BaseModel):
    """注销请求体。"""

    refresh_token: Optional[str] = Field(default=None, description="可选的刷新令牌，用于黑名单处理")


class PasswordChangeRequest(BaseModel):
    """修改密码请求体。"""

    current_password: str = Field(min_length=8, description="当前密码")
    new_password: str = Field(min_length=8, description="新密码")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        return validate_password(value)


class AccountActivationRequest(BaseModel):
    """账号激活请求体。"""

    token: str = Field(description="激活 token")
    password: str = Field(min_length=8, description="设置的新密码")

    @field_validator("password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        return validate_password(value)


class AuthenticatedResponse(ORMBaseModel):
    """携带用户信息的认证响应。"""

    token: AuthTokenPair = Field(description="Token 信息")
    user: UserRead = Field(description="登录用户信息")


class ConsultantRegisterResponse(AuthenticatedResponse):
    """顾问注册成功响应。"""

    tenant_id: str = Field(description="新创建的租户 ID")


class ActivationResponse(BaseModel):
    """账号激活成功后的响应。"""

    detail: str = Field(default="账号激活成功，请使用新密码登录")


class PasswordResetRequest(BaseModel):
    """发起密码重置请求体。"""

    email: EmailStr = Field(description="账号邮箱")


class PasswordResetConfirm(BaseModel):
    """确认密码重置请求体。"""

    token: str = Field(description="重置 token")
    password: str = Field(min_length=8, description="新的登录密码")

    @field_validator("password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        return validate_password(value)


class TokenIntrospectionResponse(BaseModel):
    """Token 自检响应体。"""

    active: bool = Field(description="Token 是否有效")
    sub: Optional[str] = Field(default=None, description="Token 对应主体 ID")
    scope: Optional[str] = Field(default=None, description="权限范围")
    expires_at: Optional[datetime] = Field(default=None, description="到期时间")
