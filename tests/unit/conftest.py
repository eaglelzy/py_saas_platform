"""Pytest 基础配置与共享 fixtures。"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import Any
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app import models  # noqa: F401  # 导入以注册所有 ORM 模型


@pytest.fixture(scope="session")
def engine() -> Generator[Any, None, None]:
    """为单元测试提供 sqlite 内存数据库引擎。"""

    engine = create_engine("sqlite+pysqlite:///:memory:", echo=False, future=True)
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def db_session(engine: Any) -> Generator[Session, None, None]:
    """快捷获取 SQLAlchemy Session。"""

    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = TestingSessionLocal()
    try:
        yield session
        session.rollback()
    finally:
        session.close()
