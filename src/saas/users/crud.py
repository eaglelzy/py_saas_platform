"""
用户管理的CRUD操作

提供用户数据的增删改查功能，包括软删除、激活/停用等业务操作。
"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from sqlalchemy.exc import IntegrityError
# 使用自定义的安全模块而不是passlib
from src.core.security import verify_password as core_verify_password, hash_password as core_hash_password
from datetime import datetime, timezone

from .user import User
from .schemas import UserCreate, UserUpdate
from src.core.exceptions import (
    BusinessLogicException,
    ResourceNotFoundException,
    DuplicateResourceException,
    DatabaseException
)

# 使用自定义的安全模块函数
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return core_verify_password(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return core_hash_password(password)


def create_user(db: Session, user: UserCreate) -> User:
    """
    创建新用户
    
    Args:
        db: 数据库会话
        user: 用户创建数据
        
    Returns:
        User: 创建的用户对象
        
    Raises:
        DuplicateResourceException: 邮箱已存在
        DatabaseException: 数据库操作失败
    """
    # 检查邮箱是否已存在
    existing_user = get_user_by_email(db, user.email)
    if existing_user:
        raise DuplicateResourceException(
            resource_type="用户",
            field="邮箱",
            value=user.email
        )
    
    try:
        # 创建用户对象
        db_user = User(
            name=user.name,
            email=user.email,
            password=get_password_hash(user.password),
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            tenant_id=user.tenant_id
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
        
    except IntegrityError as e:
        db.rollback()
        raise DatabaseException(f"数据库完整性错误: {str(e)}")
    except Exception as e:
        db.rollback()
        raise DatabaseException(f"创建用户时发生错误: {str(e)}")


def get_user(db: Session, user_id: int, include_deleted: bool = False) -> Optional[User]:
    """
    根据ID获取用户
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        include_deleted: 是否包含已删除的用户
        
    Returns:
        Optional[User]: 用户对象或None
    """
    query = db.query(User).filter(User.id == user_id)
    
    if not include_deleted:
        query = query.filter(User.is_deleted == False)
    
    return query.first()


def get_user_by_email(db: Session, email: str, include_deleted: bool = False) -> Optional[User]:
    """
    根据邮箱获取用户
    
    Args:
        db: 数据库会话
        email: 用户邮箱
        include_deleted: 是否包含已删除的用户
        
    Returns:
        Optional[User]: 用户对象或None
    """
    query = db.query(User).filter(User.email == email)
    
    if not include_deleted:
        query = query.filter(User.is_deleted == False)
    
    return query.first()


def get_users_paginated(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    only_active: bool = True,
    include_deleted: bool = False,
    tenant_id: Optional[int] = None
) -> Tuple[List[User], int]:
    """
    获取用户列表（分页）
    
    Args:
        db: 数据库会话
        skip: 跳过的记录数
        limit: 返回的记录数
        search: 搜索关键词
        sort_by: 排序字段
        sort_order: 排序方向
        only_active: 只显示激活的用户
        include_deleted: 是否包含已删除的用户
        tenant_id: 租户ID筛选
        
    Returns:
        Tuple[List[User], int]: 用户列表和总数
    """
    query = db.query(User)
    
    # 软删除筛选
    if not include_deleted:
        query = query.filter(User.is_deleted == False)
    
    # 激活状态筛选
    if only_active:
        query = query.filter(User.is_active == True)
    
    # 租户筛选
    if tenant_id is not None:
        query = query.filter(User.tenant_id == tenant_id)
    
    # 搜索功能
    if search:
        search_filter = or_(
            User.name.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # 获取总数
    total = query.count()
    
    # 排序
    if hasattr(User, sort_by):
        sort_column = getattr(User, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
    
    # 分页
    users = query.offset(skip).limit(limit).all()
    
    return users, total


def search_users(
    db: Session,
    search_params: dict,
    skip: int = 0,
    limit: int = 10
) -> Tuple[List[User], int]:
    """
    搜索用户
    
    Args:
        db: 数据库会话
        search_params: 搜索参数
        skip: 跳过的记录数
        limit: 返回的记录数
        
    Returns:
        Tuple[List[User], int]: 用户列表和总数
    """
    query = db.query(User).filter(User.is_deleted == False)
    
    # 应用搜索条件
    if search_params.get("name"):
        query = query.filter(User.name.ilike(f"%{search_params['name']}%"))
    
    if search_params.get("email"):
        query = query.filter(User.email.ilike(f"%{search_params['email']}%"))
    
    if search_params.get("is_active") is not None:
        query = query.filter(User.is_active == search_params["is_active"])
    
    if search_params.get("is_superuser") is not None:
        query = query.filter(User.is_superuser == search_params["is_superuser"])
    
    if search_params.get("tenant_id"):
        query = query.filter(User.tenant_id == search_params["tenant_id"])
    
    # 获取总数
    total = query.count()
    
    # 分页
    users = query.offset(skip).limit(limit).all()
    
    return users, total


def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """
    更新用户信息
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        user_update: 用户更新数据
        
    Returns:
        Optional[User]: 更新后的用户对象或None
        
    Raises:
        DuplicateResourceException: 邮箱已存在
        DatabaseException: 数据库操作失败
    """
    try:
        user = get_user(db, user_id)
        if not user:
            return None
        
        # 检查邮箱是否已被其他用户使用
        if user_update.email and user_update.email != user.email:
            existing_user = get_user_by_email(db, user_update.email)
            if existing_user:
                raise DuplicateResourceException(
                    resource_type="用户",
                    field="邮箱",
                    value=user_update.email
                )
        
        # 更新字段
        if user_update.name is not None:
            user.name = user_update.name
        if user_update.email is not None:
            user.email = user_update.email
        if user_update.is_active is not None:
            user.is_active = user_update.is_active
        if user_update.is_superuser is not None:
            user.is_superuser = user_update.is_superuser
        if user_update.password is not None:
            user.password = get_password_hash(user_update.password)
        
        db.commit()
        db.refresh(user)
        return user
        
    except DuplicateResourceException:
        raise
    except Exception as e:
        db.rollback()
        raise DatabaseException(f"更新用户时发生错误: {str(e)}")


def delete_user(db: Session, user_id: int) -> bool:
    """
    物理删除用户
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        bool: 删除是否成功
    """
    try:
        user = get_user(db, user_id)
        if not user:
            return False
        
        db.delete(user)
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        raise DatabaseException(f"删除用户时发生错误: {str(e)}")


def soft_delete_user(db: Session, user_id: int) -> bool:
    """
    软删除用户
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        bool: 删除是否成功
    """
    try:
        user = get_user(db, user_id)
        if not user:
            return False
        
        user.soft_delete()
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        raise DatabaseException(f"软删除用户时发生错误: {str(e)}")


def restore_user(db: Session, user_id: int) -> bool:
    """
    恢复已删除的用户
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        bool: 恢复是否成功
    """
    try:
        user = get_user(db, user_id, include_deleted=True)
        if not user or not user.is_deleted:
            return False
        
        user.restore()
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        raise DatabaseException(f"恢复用户时发生错误: {str(e)}")


def activate_user(db: Session, user_id: int) -> bool:
    """
    激活用户
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        bool: 激活是否成功
    """
    try:
        user = get_user(db, user_id)
        if not user:
            return False
        
        user.is_active = True
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        raise DatabaseException(f"激活用户时发生错误: {str(e)}")


def deactivate_user(db: Session, user_id: int) -> bool:
    """
    停用用户
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        bool: 停用是否成功
    """
    try:
        user = get_user(db, user_id)
        if not user:
            return False
        
        user.is_active = False
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        raise DatabaseException(f"停用用户时发生错误: {str(e)}")


def update_last_login(db: Session, user_id: int) -> bool:
    """
    更新用户最后登录时间
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        bool: 更新是否成功
    """
    try:
        user = get_user(db, user_id)
        if not user:
            return False
        
        user.last_login = datetime.now(timezone.utc)
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        raise DatabaseException(f"更新登录时间时发生错误: {str(e)}")


def get_user_stats(db: Session, user_id: int) -> dict:
    """
    获取用户统计信息
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        dict: 用户统计信息
    """
    user = get_user(db, user_id)
    if not user:
        return {}
    
    # 注意：Student 模型尚未创建，暂时返回 0
    # student_count = user.assigned_students.count()
    
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "tenant_name": user.tenant.name if user.tenant else "未知租户",
        "total_students": 0,  # 暂时返回 0
        "last_login": user.last_login,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }


def user_exists(db: Session, user_id: int) -> bool:
    """
    检查用户是否存在
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        bool: 用户是否存在
    """
    return get_user(db, user_id) is not None


def email_exists(db: Session, email: str) -> bool:
    """
    检查邮箱是否已存在
    
    Args:
        db: 数据库会话
        email: 邮箱地址
        
    Returns:
        bool: 邮箱是否存在
    """
    return get_user_by_email(db, email) is not None


def bulk_create_users(db: Session, users_data: List[UserCreate]) -> dict:
    """
    批量创建用户
    
    Args:
        db: 数据库会话
        users_data: 用户数据列表
        
    Returns:
        dict: 批量创建结果
    """
    success_count = 0
    failed_count = 0
    errors = []
    
    for user_data in users_data:
        try:
            create_user(db, user_data)
            success_count += 1
        except Exception as e:
            failed_count += 1
            errors.append({
                "email": user_data.email,
                "error": str(e)
            })
    
    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "errors": errors
    }


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    用户认证
    
    Args:
        db: 数据库会话
        email: 用户邮箱
        password: 用户密码
        
    Returns:
        Optional[User]: 认证成功的用户对象或None
    """
    user = get_user_by_email(db, email)
    if not user:
        return None
    
    if not verify_password(password, user.password):
        return None
    
    if not user.is_active:
        return None
    
    return user
