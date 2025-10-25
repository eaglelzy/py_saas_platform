"""SQLAlchemy Base 定义与通用字段混入。"""

from sqlalchemy import Column, DateTime, func
from sqlalchemy.orm import declarative_base

# 使用 Declarative Base 作为所有 ORM 模型的基类，便于 Alembic 自动识别
Base = declarative_base()


class TimestampMixin:
    """通用的时间戳混入类，提供创建与更新时间。"""

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="记录创建时间",
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="记录更新时间",
    )
