"""服务层分页工具。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.saas.schemas.common import PaginatedResponse, PaginationMeta

T = TypeVar("T")


@dataclass(slots=True)
class PaginationParams:
    """分页参数。"""

    page: int = 1
    size: int = 20

    def offset(self) -> int:
        return (max(self.page, 1) - 1) * max(self.size, 1)


def paginate_stmt(db: Session, stmt: Select, params: PaginationParams) -> tuple[Sequence[T], PaginationMeta]:
    """执行带分页的查询语句，并返回数据与元信息。"""

    size = max(params.size, 1)
    offset = (max(params.page, 1) - 1) * size
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar_one()
    items = db.execute(stmt.offset(offset).limit(size)).scalars().all()
    has_next = params.page * size < total
    has_prev = params.page > 1
    meta = PaginationMeta(
        total=total,
        page=params.page,
        size=size,
        has_next=has_next,
        has_prev=has_prev,
    )
    return items, meta


def build_paginated_response(items: Sequence[T], meta: PaginationMeta) -> PaginatedResponse[T]:
    """将查询结果组装成分页响应体。"""

    return PaginatedResponse[T](items=list(items), meta=meta)
