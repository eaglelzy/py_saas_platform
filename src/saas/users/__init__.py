"""
用户管理模块

提供用户管理的完整功能，包括：
- 数据模型 (user.py)
- 业务逻辑 (crud.py)
- API 接口 (api.py)
- 数据验证 (schemas.py)
"""

from .api import router
from .crud import *
from .schemas import *
from .user import User

__all__ = [
    "router",
    "User",
    # CRUD functions
    "create_user",
    "get_user",
    "get_user_by_email",
    "get_users_paginated",
    "search_users",
    "update_user",
    "delete_user",
    "soft_delete_user",
    "restore_user",
    "activate_user",
    "deactivate_user",
    "update_last_login",
    "get_user_stats",
    "user_exists",
    "email_exists",
    "bulk_create_users",
    "authenticate_user",
    "verify_password",
    "get_password_hash",
    # Schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",
    "UserPasswordChange",
    "UserActivate",
    "UserDeactivate",
    "UserStats",
    "UserSearchParams",
    "UserBulkCreate",
    "UserBulkResponse",
    "UserLogin",
    "UserLoginResponse"
]
