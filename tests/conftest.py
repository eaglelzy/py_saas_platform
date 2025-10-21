"""
测试配置文件

提供测试所需的 fixtures 和配置。
"""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# 设置测试环境变量
os.environ.setdefault("ENV", "unit-test")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("LOG_LEVEL", "DEBUG")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")

from src.core.db import Base, get_db
from src.main import app
from src.saas.tenants.tanant import Tenant
from src.saas.users.user import User


# 测试数据库配置
engine = create_engine(os.environ.get("DATABASE_URL"), connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    """数据库引擎 fixture"""
    return engine


@pytest.fixture(scope="function")
def db(db_engine):
    """数据库会话 fixture"""
    # 创建表
    Base.metadata.create_all(bind=db_engine)
    
    # 创建会话
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        # 清理表
        Base.metadata.drop_all(bind=db_engine)


@pytest.fixture
def client(db):
    """测试客户端 fixture"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def test_tenant(db: TestingSessionLocal) -> Tenant:
    """测试租户 fixture"""
    tenant = Tenant(name="测试租户")
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@pytest.fixture
def test_tenants(db: TestingSessionLocal) -> list[Tenant]:
    """多个测试租户 fixture"""
    tenants = [
        Tenant(name="测试租户1"),
        Tenant(name="测试租户2"),
        Tenant(name="测试租户3"),
        Tenant(name="ABC_教育公司"),
        Tenant(name="XYZ_培训机构")
    ]
    
    for tenant in tenants:
        db.add(tenant)
    db.commit()
    
    for tenant in tenants:
        db.refresh(tenant)
    
    return tenants


@pytest.fixture
def test_user(db: TestingSessionLocal, test_tenant: Tenant) -> User:
    """测试用户 fixture"""
    user = User(
        name="测试用户",
        email="test@example.com",
        password="hashed_password",
        tenant_id=test_tenant.id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user