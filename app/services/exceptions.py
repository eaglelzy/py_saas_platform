# app/services/exceptions.py
"""服务层统一异常定义。"""

from __future__ import annotations

from fastapi import status


class ServiceError(Exception):
    """服务层基础异常。"""
    
    # 默认状态码，子类可以覆盖
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        # 自动获取类属性中的 status_code
        self.status_code = self.__class__.status_code
        self.code = code


class NotFoundError(ServiceError):
    """资源不存在异常。"""
    status_code = status.HTTP_404_NOT_FOUND


class ConflictError(ServiceError):
    """冲突异常，例如重复数据或状态冲突。"""
    status_code = status.HTTP_409_CONFLICT


class ValidationError(ServiceError):
    """业务校验失败。"""
    status_code = status.HTTP_400_BAD_REQUEST


class PermissionDeniedError(ServiceError):
    """权限不足。"""
    status_code = status.HTTP_403_FORBIDDEN