"""
自定义异常类

定义应用程序中使用的各种异常类型，提供结构化的错误处理。
"""

from typing import Any, Dict, Optional
from fastapi import status


class BaseAPIException(Exception):
    """
    基础API异常类
    
    所有自定义异常的基类，提供统一的异常处理接口。
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(BaseAPIException):
    """
    数据验证异常
    
    当输入数据不符合预期格式或规则时抛出。
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            details=details
        )


class BusinessLogicException(BaseAPIException):
    """
    业务逻辑异常
    
    当业务规则被违反时抛出。
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="BUSINESS_LOGIC_ERROR",
            details=details
        )


class ResourceNotFoundException(BaseAPIException):
    """
    资源未找到异常
    
    当请求的资源不存在时抛出。
    """
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[str] = None,
        resource_field: Optional[str] = None,
        resource_value: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if resource_id is not None:
            message = f"{resource_type} (ID: {resource_id}) 不存在"
        elif resource_field and resource_value:
            message = f"{resource_type} ({resource_field}: {resource_value}) 不存在"
        else:
            message = f"{resource_type} 不存在"
            
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            details=details
        )


class DuplicateResourceException(BaseAPIException):
    """
    重复资源异常
    
    当尝试创建已存在的资源时抛出。
    """
    
    def __init__(
        self,
        resource_type: str,
        field: str,
        value: str,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"{resource_type} {field} '{value}' 已存在"
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="DUPLICATE_RESOURCE",
            details=details
        )


class DatabaseException(BaseAPIException):
    """
    数据库异常
    
    当数据库操作失败时抛出。
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            details=details
        )


class ExternalServiceException(BaseAPIException):
    """
    外部服务异常
    
    当调用外部服务失败时抛出。
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details
        )


class PermissionDeniedException(BaseAPIException):
    """
    权限拒绝异常
    
    当用户没有足够权限执行操作时抛出。
    """
    
    def __init__(self, message: str = "权限不足", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="PERMISSION_DENIED",
            details=details
        )


class AuthenticationException(BaseAPIException):
    """
    认证异常
    
    当用户认证失败时抛出。
    """
    
    def __init__(self, message: str = "认证失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_FAILED",
            details=details
        )


class RateLimitException(BaseAPIException):
    """
    速率限制异常
    
    当请求频率超过限制时抛出。
    """
    
    def __init__(self, message: str = "请求过于频繁", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details
        )
