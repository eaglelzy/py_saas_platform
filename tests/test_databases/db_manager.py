# tests/test_databases/db_manager.py
"""
测试数据库管理器

提供测试数据库的创建、管理和清理功能。
"""

import os
import tempfile
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine


class TestDatabaseManager:
    """测试数据库管理器"""
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        初始化测试数据库管理器
        
        Args:
            base_dir: 测试数据库基础目录，默认为 tests/test_databases
        """
        if base_dir is None:
            base_dir = os.path.join(os.path.dirname(__file__), "test_databases")
        
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
    
    def create_test_database(self, test_name: str) -> tuple[Engine, sessionmaker]:
        """
        为特定测试创建数据库
        
        Args:
            test_name: 测试名称，用于生成唯一的数据库文件名
            
        Returns:
            tuple: (engine, session_factory) 数据库引擎和会话工厂
        """
        # 生成测试数据库文件路径
        db_path = os.path.join(self.base_dir, f"{test_name}.db")
        
        # 创建数据库引擎
        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False}
        )
        
        # 创建会话工厂
        session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        
        return engine, session_factory
    
    def create_temp_database(self) -> tuple[Engine, sessionmaker, str]:
        """
        创建临时测试数据库
        
        Returns:
            tuple: (engine, session_factory, db_path) 数据库引擎、会话工厂和数据库路径
        """
        # 创建临时文件
        temp_fd, temp_path = tempfile.mkstemp(suffix='.db', dir=self.base_dir)
        os.close(temp_fd)
        
        # 创建数据库引擎
        engine = create_engine(
            f"sqlite:///{temp_path}",
            connect_args={"check_same_thread": False}
        )
        
        # 创建会话工厂
        session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        
        return engine, session_factory, temp_path
    
    def cleanup_database(self, db_path: str):
        """
        清理测试数据库文件
        
        Args:
            db_path: 数据库文件路径
        """
        if os.path.exists(db_path):
            os.remove(db_path)
    
    def cleanup_all_databases(self):
        """清理所有测试数据库文件"""
        if os.path.exists(self.base_dir):
            for file in os.listdir(self.base_dir):
                if file.endswith('.db'):
                    file_path = os.path.join(self.base_dir, file)
                    os.remove(file_path)
    
    def get_database_list(self) -> list[str]:
        """
        获取所有测试数据库文件列表
        
        Returns:
            list: 数据库文件路径列表
        """
        if not os.path.exists(self.base_dir):
            return []
        
        db_files = []
        for file in os.listdir(self.base_dir):
            if file.endswith('.db'):
                db_files.append(os.path.join(self.base_dir, file))
        
        return db_files


# 全局测试数据库管理器实例
test_db_manager = TestDatabaseManager()
