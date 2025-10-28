"""数据库引擎与会话管理。"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.saas.core.config.settings import settings


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """提供数据库会话依赖，确保生命周期管理。"""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
