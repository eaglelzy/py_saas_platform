"""Pydantic schema 层的通用类型与基类定义。"""

from __future__ import annotations

from datetime import datetime
from typing import Generic, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field


class ORMBaseModel(BaseModel):
    """默认开启 ORM 模式的 BaseModel，方便与 SQLAlchemy 模型互转。"""

    model_config = {
        "from_attributes": True,
        "use_enum_values": True,
        "populate_by_name": True,
    }


class TimestampMixin(BaseModel):
    """提供统一的时间戳字段序列化。"""

    created_at: datetime = Field(
        description="记录创建时间",
        json_schema_extra={"example": "2025-01-01T08:00:00+00:00"},
    )
    updated_at: datetime = Field(
        description="记录更新时间",
        json_schema_extra={"example": "2025-01-02T09:30:00+00:00"},
    )


class IDMixin(BaseModel):
    """统一的主键字段约定，使用 UUID 类型。"""

    id: UUID = Field(
        description="实体主键，UUID",
        json_schema_extra={"example": "7f04b42c-2f78-4f78-897c-1d957533fb44"},
    )


T = TypeVar("T")

class PaginationRequestMeta(BaseModel):
    """分页元数据。"""

    page: int = Field(ge=1, description="当前页码，从 1 开始")
    size: int = Field(ge=1, le=100, description="每页大小，范围 1-100")


class PaginationMeta(BaseModel):
    """分页元数据。"""

    total: int = Field(ge=0, description="总记录数")
    page: int = Field(ge=1, description="当前页码，从 1 开始")
    size: int = Field(ge=1, description="每页大小")
    has_next: bool = Field(description="是否存在下一页")
    has_prev: bool = Field(description="是否存在上一页")


class PaginatedResponse(ORMBaseModel, Generic[T]):
    """泛型分页响应体，包含数据列表与分页信息。"""

    items: list[T] = Field(default_factory=list, description="当前页数据列表")
    meta: PaginationMeta = Field(description="分页元数据")


class ErrorResponse(BaseModel):
    """统一错误响应体。"""

    code: Optional[str] = Field(default=None, description="业务错误码，可选")
    message: str = Field(description="错误详情信息")

class SuccessResponse(BaseModel):
    """统一成功响应体。"""

    message: str = Field(description="成功信息")


class FieldError(BaseModel):
    """字段级的错误描述。"""

    field: str = Field(description="字段路径")
    message: str = Field(description="错误提示")


class ValidationErrorResponse(ErrorResponse):
    """带字段列表的校验错误响应。"""

    detail: list[FieldError] = Field(default_factory=list, description="字段错误列表")
