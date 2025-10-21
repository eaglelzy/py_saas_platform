"""
认证相关的数据模型
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class LoginRequest(BaseModel):
    """登录请求"""
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str

class UserInfo(BaseModel):
    """用户信息"""
    id: int
    name: str
    email: str
    is_active: bool
    is_superuser: bool
    tenant_id: int
    last_login: Optional[datetime] = None

class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInfo

class LogoutRequest(BaseModel):
    """登出请求"""
    access_token: str

class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    current_password: str
    new_password: str