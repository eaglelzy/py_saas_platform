"""
认证服务模块
处理用户认证、令牌管理等业务逻辑
"""

from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.saas.users import crud as user_crud
from src.saas.auth.jwt_utils import jwt_manager
from src.saas.auth.schemas import LoginRequest, LoginResponse, UserInfo, TokenResponse
from src.core.logging import get_logger

logger = get_logger(__name__)

class AuthService:
    """认证服务类"""
    
    def __init__(self):
        self.jwt_manager = jwt_manager
    
    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[dict]:
        """
        验证用户凭据
        
        Args:
            db: 数据库会话
            email: 用户邮箱
            password: 用户密码
            
        Returns:
            Optional[dict]: 用户信息，验证失败返回None
        """
        user = user_crud.get_user_by_email(db, email)
        if not user:
            logger.warning(f"用户不存在: {email}")
            return None
        
        if not user.is_active:
            logger.warning(f"用户账户未激活: {email}")
            return None
        
        if not self.jwt_manager.verify_password(password, user.password):
            logger.warning(f"密码验证失败: {email}")
            return None
        
        # 更新最后登录时间
        user_crud.update_last_login(db, user.id)
        
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "tenant_id": user.tenant_id,
            "last_login": user.last_login
        }
    
    def login(self, db: Session, login_data: LoginRequest) -> LoginResponse:
        """
        用户登录
        
        Args:
            db: 数据库会话
            login_data: 登录数据
            
        Returns:
            LoginResponse: 登录响应
            
        Raises:
            HTTPException: 认证失败
        """
        user_info = self.authenticate_user(db, login_data.email, login_data.password)
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 创建令牌数据
        token_data = {
            "sub": str(user_info["id"]),
            "email": user_info["email"],
            "tenant_id": user_info["tenant_id"],
            "is_superuser": user_info["is_superuser"]
        }
        
        # 生成访问令牌和刷新令牌
        access_token = self.jwt_manager.create_access_token(token_data)
        refresh_token = self.jwt_manager.create_refresh_token(token_data)
        
        logger.info(f"用户登录成功: {user_info['email']}")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=3600,  # 1小时
            user=UserInfo(**user_info)
        )
    
    def refresh_token(self, db: Session, refresh_token: str) -> TokenResponse:
        """
        刷新访问令牌
        
        Args:
            db: 数据库会话
            refresh_token: 刷新令牌
            
        Returns:
            TokenResponse: 新的令牌响应
            
        Raises:
            HTTPException: 令牌无效
        """
        # 使用专门的刷新令牌验证方法
        payload = self.jwt_manager.verify_refresh_token(refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌或令牌已过期",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 验证用户是否仍然存在且激活
        user_id = int(payload["sub"])
        user = user_crud.get_user(db, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已停用",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 生成新的访问令牌
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "tenant_id": user.tenant_id,
            "is_superuser": user.is_superuser
        }
        
        access_token = self.jwt_manager.create_access_token(token_data)
        
        logger.info(f"令牌刷新成功: {user.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,  # 刷新令牌保持不变
            expires_in=3600
        )
    
    def get_current_user(self, db: Session, token: str) -> dict:
        """
        从令牌获取当前用户信息
        
        Args:
            db: 数据库会话
            token: JWT令牌
            
        Returns:
            dict: 用户信息
            
        Raises:
            HTTPException: 令牌无效或用户不存在
        """
        payload = self.jwt_manager.verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的访问令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = int(payload["sub"])
        user = user_crud.get_user(db, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已停用",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "tenant_id": user.tenant_id,
            "last_login": user.last_login
        }

# 创建全局认证服务实例
auth_service = AuthService()