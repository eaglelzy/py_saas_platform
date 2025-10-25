"""认证与授权相关 schema。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.common import ORMBaseModel
from app.utils import validate_password
from app.schemas.users import UserRead


class AuthLoginRequest(BaseModel):
    """登录请求体。"""

    email: EmailStr = Field(description="登录邮箱")
    password: str = Field(min_length=8, description="登录密码")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> EmailStr:
        return EmailStr(str(value).lower())


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
