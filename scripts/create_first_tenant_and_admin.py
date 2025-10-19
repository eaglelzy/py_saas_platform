#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建第一个租户的脚本

这个脚本用于在系统中创建第一个租户，通常用于系统初始化。
租户是 SaaS 平台中的核心概念，代表一个独立的企业或组织。

使用方法：
    python scripts/create_first_tenant.py

功能：
- 创建系统第一个租户
- 验证租户名称的唯一性
- 提供详细的创建日志
- 支持命令行参数自定义租户名称
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from src.core.db import SessionLocal, engine
from src.core.db import Base
from src.saas.tenants.tanant import Tenant
from src.saas.users.user import User
from src.core.logging import get_logger, setup_logging

def create_first_tenant(db: Session, name: str):
    """
    创建第一个租户的函数
    
    Args:
        db (Session): 数据库会话对象
        name (str): 租户名称
        
    Returns:
        Tenant: 创建的租户对象
        
    Raises:
        ValueError: 当租户名称已存在时抛出异常
    """
    logger = get_logger(__name__)
    
    logger.info(f"🔍 检查租户 '{name}' 是否已存在...")
    
    # 检查租户是否已存在
    existing_tenant = db.query(Tenant).filter(Tenant.name == name).first()
    if existing_tenant:
        logger.warning(f"租户 '{name}' 已存在，ID: {existing_tenant.id}")
        raise ValueError(f"租户 '{name}' 已存在，ID: {existing_tenant.id}")
    
    logger.info(f"✅ 租户名称 '{name}' 可用，开始创建...")
    
    # 创建新租户
    tenant = Tenant(name=name)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)  # 刷新以获取生成的 ID
    
    logger.info(f"🎉 租户创建成功！")
    logger.info(f"   - 租户名称: {tenant.name}")
    logger.info(f"   - 租户ID: {tenant.id}")
    
    return tenant


def create_initial_admin_user(db: Session, tenant_id: int, admin_name: str, admin_email: str, admin_password: str):
    """
    为租户创建初始管理员用户
    
    Args:
        db (Session): 数据库会话对象
        tenant_id (int): 租户ID
        admin_name (str): 管理员姓名
        admin_email (str): 管理员邮箱
        admin_password (str): 管理员密码（已加密）
        
    Returns:
        User: 创建的管理员用户对象
    """
    logger = get_logger(__name__)
    
    logger.info(f"👤 为租户 {tenant_id} 创建初始管理员用户...")
    
    # 检查邮箱是否已存在
    existing_user = db.query(User).filter(User.email == admin_email).first()
    if existing_user:
        logger.warning(f"邮箱 '{admin_email}' 已被使用")
        raise ValueError(f"邮箱 '{admin_email}' 已被使用")
    
    # 创建管理员用户
    admin_user = User(
        name=admin_name,
        email=admin_email,
        password=admin_password,  # 注意：这里应该是加密后的密码
        is_active=True,
        is_superuser=True,  # 设置为超级用户
        tenant_id=tenant_id
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    logger.info(f"🎉 管理员用户创建成功！")
    logger.info(f"   - 用户姓名: {admin_user.name}")
    logger.info(f"   - 用户邮箱: {admin_user.email}")
    logger.info(f"   - 用户ID: {admin_user.id}")
    logger.info(f"   - 租户ID: {admin_user.tenant_id}")
    logger.info(f"   - 超级用户: {admin_user.is_superuser}")
    logger.info(f"   - 创建时间: {admin_user.created_at}")
    
    return admin_user


def init_database():
    """
    初始化数据库表结构
    
    创建所有必要的数据库表。
    """
    logger = get_logger(__name__)
    
    logger.info("🗄️  初始化数据库表结构...")
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    logger.info("✅ 数据库表结构创建完成！")


def main():
    """
    主函数：创建第一个租户和初始管理员
    
    这个函数会：
    1. 初始化数据库表结构
    2. 创建第一个租户
    3. 为租户创建初始管理员用户
    4. 提供详细的创建日志
    """
    # 设置日志
    setup_logging(log_level="INFO", use_colors=True)
    logger = get_logger(__name__)
    
    logger.info("=" * 60)
    logger.info("🚀 开始创建第一个租户和初始管理员")
    logger.info("=" * 60)
    
    # 默认配置
    tenant_name = "默认租户"
    admin_name = "系统管理员"
    admin_email = "admin@example.com"
    admin_password = "admin123"  # 注意：生产环境中应该使用加密密码
    
    # 可以通过环境变量或命令行参数覆盖默认值
    tenant_name = os.getenv("TENANT_NAME", tenant_name)
    admin_email = os.getenv("ADMIN_EMAIL", admin_email)
    admin_password = os.getenv("ADMIN_PASSWORD", admin_password)
    
    logger.info(f"📋 创建配置：")
    logger.info(f"   - 租户名称: {tenant_name}")
    logger.info(f"   - 管理员姓名: {admin_name}")
    logger.info(f"   - 管理员邮箱: {admin_email}")
    logger.info(f"   - 管理员密码: {'*' * len(admin_password)}")
    logger.info("")
    
    try:
        # 初始化数据库
        init_database()
        
        # 创建数据库会话
        db = SessionLocal()
        
        try:
            # 创建第一个租户
            tenant = create_first_tenant(db, tenant_name)
            
            # 创建初始管理员用户
            admin_user = create_initial_admin_user(
                db, 
                tenant.id, 
                admin_name, 
                admin_email, 
                admin_password
            )
            
            logger.info("")
            logger.info("=" * 60)
            logger.info("🎉 系统初始化完成！")
            logger.info("=" * 60)
            logger.info(f"✅ 租户创建成功: {tenant.name} (ID: {tenant.id})")
            logger.info(f"✅ 管理员创建成功: {admin_user.name} (ID: {admin_user.id})")
            logger.info("")
            logger.info("📝 登录信息：")
            logger.info(f"   - 邮箱: {admin_email}")
            logger.info(f"   - 密码: {admin_password}")
            logger.info("")
            logger.info("⚠️  请在生产环境中立即修改默认密码！")
            
        except Exception as e:
            logger.error(f"❌ 创建过程中发生错误: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"💥 系统初始化失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
