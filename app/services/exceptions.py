# app/services/exceptions.py
"""服务层统一异常定义。"""

from __future__ import annotations

from fastapi import status


class ServiceError(Exception):
    """服务层基础异常。"""

    # 默认状态码和错误编码前缀，子类可覆盖
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_code = "SERVICE_ERROR"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        context: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = self.__class__.status_code
        self.code = code or self.__class__.default_code
        self.context = context or {}

    def to_dict(self) -> dict[str, object]:
        """统一响应结构，方便转为 HTTPException detail。"""
        payload: dict[str, object] = {"code": self.code, "message": str(self)}
        # if self.context:
            # payload["context"] = self.context
        return payload

class UnauthorizedError(ServiceError):
    """未授权异常。"""
    status_code = status.HTTP_401_UNAUTHORIZED
    default_code = "UNAUTHORIZED"

class ForbiddenError(ServiceError):
    """禁止访问异常。"""
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "FORBIDDEN"

class NotFoundError(ServiceError):
    """资源不存在异常。"""
    status_code = status.HTTP_404_NOT_FOUND
    default_code = "NOT_FOUND"


class ConflictError(ServiceError):
    """冲突异常，例如重复数据或状态冲突。"""
    status_code = status.HTTP_409_CONFLICT
    default_code = "CONFLICT"


class ValidationError(ServiceError):
    """业务校验失败。"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "VALIDATION_ERROR"


class PermissionDeniedError(ServiceError):
    """权限不足。"""
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "PERMISSION_DENIED"
