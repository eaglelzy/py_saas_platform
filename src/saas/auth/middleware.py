"""
认证中间件
提供JWT令牌验证和用户信息注入
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from src.core.db import get_db
from src.saas.auth.service import auth_service
from src.core.logging import get_logger

logger = get_logger(__name__)

# HTTP Bearer 安全方案
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """
    获取当前认证用户
    
    Args:
        credentials: HTTP认证凭据
        db: 数据库会话
        
    Returns:
        dict: 当前用户信息
        
    Raises:
        HTTPException: 认证失败
    """
    token = credentials.credentials
    return auth_service.get_current_user(db, token)

def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """
    获取当前激活用户
    
    Args:
        current_user: 当前用户信息
        
    Returns:
        dict: 激活的用户信息
        
    Raises:
        HTTPException: 用户未激活
    """
    if not current_user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户未激活"
        )
    return current_user

def get_current_superuser(current_user: dict = Depends(get_current_user)) -> dict:
    """
    获取当前超级用户
    
    Args:
        current_user: 当前用户信息
        
    Returns:
        dict: 超级用户信息
        
    Raises:
        HTTPException: 权限不足
    """
    if not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级用户权限"
        )
    return current_user

def get_current_tenant_user(current_user: dict = Depends(get_current_user)) -> dict:
    """
    获取当前租户用户（非超级用户）
    
    Args:
        current_user: 当前用户信息
        
    Returns:
        dict: 租户用户信息
        
    Raises:
        HTTPException: 权限不足
    """
    if current_user.get("is_superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="超级用户无法访问租户功能"
        )
    return current_user