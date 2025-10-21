"""
JWT工具模块
提供JWT令牌的生成、验证、刷新等功能
适配现有的core.security.py密码哈希系统
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from src.core.config import settings
from src.core.security import verify_password, hash_password
from src.core.logging import get_logger

logger = get_logger(__name__)

class JWTManager:
    """JWT令牌管理器"""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        创建访问令牌
        
        Args:
            data: 要编码到令牌中的数据
            expires_delta: 过期时间增量
            
        Returns:
            str: JWT访问令牌
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        logger.info(f"创建访问令牌成功，用户ID: {data.get('sub', 'unknown')}")
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        创建刷新令牌（有效期更长）
        
        Args:
            data: 要编码到令牌中的数据
            
        Returns:
            str: JWT刷新令牌
        """
        to_encode = data.copy()
        # 刷新令牌有效期7天
        expire = datetime.now(timezone.utc) + timedelta(days=7)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        logger.info(f"创建刷新令牌成功，用户ID: {data.get('sub', 'unknown')}")
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证JWT令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            Optional[Dict]: 解码后的令牌数据，验证失败返回None
        """
        # 处理None值和空字符串
        if not token:
            logger.warning("JWT令牌为空或None")
            return None
            
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.warning(f"JWT令牌验证失败: {str(e)}")
            return None
    
    def verify_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证刷新令牌（专门的刷新令牌验证方法）
        
        Args:
            token: 刷新令牌
            
        Returns:
            Optional[Dict]: 解码后的令牌数据，验证失败返回None
        """
        # 先进行基本的JWT验证（包括过期时间、签名、算法检查）
        payload = self.verify_token(token)
        if not payload:
            return None
        
        # 验证令牌类型（JWT库不会检查自定义字段）
        if payload.get("type") != "refresh":
            logger.warning("令牌不是有效的刷新令牌")
            return None
        
        # 验证刷新令牌的必要字段
        if "sub" not in payload:
            logger.warning("刷新令牌缺少用户ID")
            return None
        
        logger.info(f"刷新令牌验证成功，用户ID: {payload.get('sub')}")
        return payload
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        验证密码（使用现有的安全模块）
        
        Args:
            plain_password: 明文密码
            hashed_password: 哈希密码
            
        Returns:
            bool: 密码是否正确
        """
        return verify_password(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """
        生成密码哈希（使用现有的安全模块）
        
        Args:
            password: 明文密码
            
        Returns:
            str: 哈希后的密码
        """
        return hash_password(password)

# 创建全局JWT管理器实例
jwt_manager = JWTManager()