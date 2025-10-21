# tests/test_databases/pytest_plugin.py
"""
Pytest插件：自动管理测试数据库

提供测试数据库的自动创建和清理功能。
"""

import os
import pytest
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine

from .db_manager import TestDatabaseManager


class TestDatabasePlugin:
    """测试数据库Pytest插件"""
    
    def __init__(self):
        self.db_manager = TestDatabaseManager()
        self.created_databases = []
    
    def pytest_runtest_setup(self, item):
        """测试开始前设置"""
        # 为每个测试创建独立的数据库
        test_name = item.name.replace("::", "_").replace(" ", "_")
        engine, session_factory = self.db_manager.create_test_database(test_name)
        
        # 存储数据库信息
        self.created_databases.append({
            'test_name': test_name,
            'engine': engine,
            'session_factory': session_factory
        })
    
    def pytest_runtest_teardown(self, item):
        """测试结束后清理"""
        # 清理测试数据库
        test_name = item.name.replace("::", "_").replace(" ", "_")
        db_path = os.path.join(self.db_manager.base_dir, f"{test_name}.db")
        self.db_manager.cleanup_database(db_path)
    
    def pytest_sessionfinish(self, session, exitstatus):
        """测试会话结束时清理所有数据库"""
        self.db_manager.cleanup_all_databases()


@pytest.fixture(scope="function")
def test_db_engine():
    """测试数据库引擎fixture"""
    db_manager = TestDatabaseManager()
    engine, session_factory = db_manager.create_temp_database()
    yield engine
    # 测试完成后自动清理
    db_manager.cleanup_database(engine.url.database)


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """测试数据库会话fixture"""
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine
    )
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def pytest_configure(config):
    """Pytest配置"""
    # 注册插件
    plugin = TestDatabasePlugin()
    config.pluginmanager.register(plugin, "test_database_plugin")
