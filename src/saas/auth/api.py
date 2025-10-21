"""
认证API端点
提供登录、登出、令牌刷新等认证相关接口
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.core.db import get_db
from src.saas.auth.service import auth_service
from src.saas.auth.schemas import (
    LoginRequest, LoginResponse, RefreshTokenRequest, 
    TokenResponse, LogoutRequest, ChangePasswordRequest
)
from src.saas.auth.middleware import get_current_user
from src.core.logging import get_logger

router = APIRouter(prefix="/auth")
logger = get_logger(__name__)

@router.post("/login", response_model=LoginResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    用户登录
    
    Args:
        login_data: 登录数据
        db: 数据库会话
        
    Returns:
        LoginResponse: 登录响应（包含访问令牌和刷新令牌）
        
    Raises:
        HTTPException: 401 - 认证失败
    """
    return auth_service.login(db, login_data)

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    refresh_data: RefreshTokenRequest, 
    db: Session = Depends(get_db)
):
    """
    刷新访问令牌
    
    Args:
        refresh_data: 刷新令牌数据
        db: 数据库会话
        
    Returns:
        TokenResponse: 新的令牌响应
        
    Raises:
        HTTPException: 401 - 令牌无效
    """
    return auth_service.refresh_token(db, refresh_data.refresh_token)

@router.post("/logout")
def logout(logout_data: LogoutRequest, current_user: dict = Depends(get_current_user)):
    """
    用户登出
    
    Args:
        logout_data: 登出数据
        current_user: 当前用户信息
        
    Returns:
        dict: 登出确认
    """
    # 这里可以实现令牌黑名单机制
    logger.info(f"用户登出: {current_user['email']}")
    return {"message": "登出成功"}

@router.get("/me")
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    获取当前用户信息
    
    Args:
        current_user: 当前用户信息
        
    Returns:
        dict: 用户信息
    """
    return current_user

@router.post("/change-password")
def change_password(
    password_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改当前用户密码
    
    Args:
        password_data: 密码修改数据
        current_user: 当前用户信息
        db: 数据库会话
        
    Returns:
        dict: 修改结果
        
    Raises:
        HTTPException: 当前密码错误
    """
    success = auth_service.change_password(db, current_user["id"], password_data)
    return {"message": "密码修改成功"}

@router.get("/test")
def auth_test():
    """测试认证接口"""
    logger.info("收到认证测试请求")
    return {"message": "Auth router is working!"}