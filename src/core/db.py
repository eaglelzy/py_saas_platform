# src/core/db.py

from typing import Generator
from sqlalchemy import create_engine, Column, DateTime, func
# sessionmaker 用于创建 Session 工厂
# Session 是与数据库交互的主要句柄
# declarative_base 是创建模型基类的工厂函数
# declared_attr 用于在 mixin 类中定义动态属性
from sqlalchemy.orm import sessionmaker, Session, declarative_base, declared_attr

# 从我们刚刚定义的 config 文件中导入全局 settings 实例
from .config import settings

# 1. 创建 SQLAlchemy engine
# --------------------------------------------------------------------------
# engine 是 SQLAlchemy 与数据库后端建立连接的核心接口。
# 它维护了一个连接池，为应用提供数据库连接。
# `pool_pre_ping=True` 是一个重要的生产实践。它确保每次从池中取出的连接
# 都是“鲜活”的，能有效避免因网络问题或数据库重启导致的连接失效错误。
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True
)

# 2. 创建 SessionLocal 类
# --------------------------------------------------------------------------
# 我们不直接使用 engine，而是通过“会话(Session)”来与数据库交互。
# sessionmaker 创建了一个 Session “工厂”，我们可以用它来按需生产 Session。
# autocommit=False 和 autoflush=False 让我们对事务有完全的控制权，
# 只有当我们显式调用 `db.commit()` 时，改动才会被提交。
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 3. 创建 Base 类
# --------------------------------------------------------------------------
# 这是所有数据模型（ORM classes）的“元祖”。
# 我们定义的每一个模型，比如 User, Student, Article，都必须继承自这个 Base。
# 这就是 SQLAlchemy 和 Alembic 如何知道哪些 Python 类需要被映射成数据库表的机制。
Base = declarative_base()

# 3.5. 创建 TimestampMixin 类
# --------------------------------------------------------------------------
# 这是一个 Mixin 类，提供了自动时间戳功能。
# 任何继承此类的模型都会自动获得 created_at 和 updated_at 字段。
# 
# 使用 @declared_attr 装饰器的原因：
# - 确保每个继承该 Mixin 的模型都获得独立的时间戳列
# - 避免列名冲突，每个模型都有自己独立的 created_at 和 updated_at 字段
# - 支持多继承场景下的正确行为
class TimestampMixin:
    """
    时间戳 Mixin 类，为模型提供自动的时间戳字段。
    
    使用方法：
    ```python
    class User(Base, TimestampMixin):
        __tablename__ = "users"
        id = Column(Integer, primary_key=True)
        name = Column(String(50))
        # created_at 和 updated_at 字段会自动添加
    ```
    
    特性：
    - created_at: 记录创建时间，使用 server_default=func.now() 在数据库层面设置默认值
    - updated_at: 记录最后更新时间，每次记录更新时自动更新
    """
    
    @declared_attr
    def created_at(cls):
        """
        创建时间字段。
        使用 server_default=func.now() 确保在数据库层面设置默认值，
        这样即使绕过 ORM 直接插入数据也能正确设置创建时间。
        """
        return Column(DateTime, server_default=func.now(), nullable=False)

    @declared_attr
    def updated_at(cls):
        """
        更新时间字段。
        - server_default=func.now(): 初始创建时设置默认值
        - onupdate=func.now(): 每次记录更新时自动更新此字段
        """
        return Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


# 4. 为 FastAPI 创建数据库会话的依赖项
# --------------------------------------------------------------------------
# 这是一个 Python 的生成器函数，被设计为 FastAPI 的依赖项 (Dependency)。
def get_db() -> Generator[Session, None, None]:
    """
    这个函数是连接 FastAPI 和 SQLAlchemy 的桥梁。

    当一个 API 请求到达时，FastAPI 会调用这个函数:
    1. `db = SessionLocal()`: 创建一个新的数据库会话。
    2. `yield db`: 将这个会话“产出”给路径操作函数（你的 API 接口）。
    3. 接口函数执行它的逻辑，使用这个 `db` 对象进行数据库操作。
    4. 请求结束后，无论成功还是异常，`finally` 块中的 `db.close()`
       都必定会执行，从而将数据库连接释放回连接池。

    这个模式优雅地处理了会话的生命周期，是 FastAPI + SQLAlchemy 的最佳实践。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
