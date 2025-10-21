"""
租户（Tenant）CRUD 操作

提供租户的创建、读取、更新、删除等数据库操作。
"""

from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from sqlalchemy.exc import IntegrityError

from src.saas.tenants.tanant import Tenant
from src.saas.tenants.schemas import TenantCreate, TenantUpdate
from src.core.exceptions import (
    BusinessLogicException,
    ResourceNotFoundException,
    DuplicateResourceException,
    DatabaseException
)


def create_tenant(db: Session, tenant: TenantCreate) -> Tenant:
    """
    创建新租户
    
    Args:
        db: 数据库会话
        tenant: 租户创建数据
        
    Returns:
        Tenant: 创建的租户对象
        
    Raises:
        DuplicateResourceException: 如果租户名称已存在
        DatabaseException: 数据库操作失败
    """
    # 检查租户名称是否已存在
    existing_tenant = get_tenant_by_name(db, tenant.name)
    if existing_tenant:
        raise DuplicateResourceException(
            resource_type="租户",
            field="名称",
            value=tenant.name
        )
    
    try:
        db_tenant = Tenant(name=tenant.name)
        db.add(db_tenant)
        db.commit()
        db.refresh(db_tenant)
        return db_tenant
        
    except IntegrityError as e:
        db.rollback()
        raise DatabaseException(f"数据库完整性错误: {str(e)}")
    except Exception as e:
        db.rollback()
        raise DatabaseException(f"创建租户时发生错误: {str(e)}")


def get_tenant(db: Session, tenant_id: int, include_deleted: bool = False) -> Optional[Tenant]:
    """
    获取单个租户
    
    Args:
        db: 数据库会话
        tenant_id: 租户ID
        include_deleted: 是否包含已删除的租户
        
    Returns:
        Optional[Tenant]: 租户对象，不存在则返回 None
    """
    query = db.query(Tenant).filter(Tenant.id == tenant_id)
    
    if not include_deleted:
        query = query.filter(Tenant.is_deleted == False)
    
    return query.first()


def get_tenant_by_name(db: Session, name: str, include_deleted: bool = False) -> Optional[Tenant]:
    """
    根据名称获取租户
    
    Args:
        db: 数据库会话
        name: 租户名称
        include_deleted: 是否包含已删除的租户
        
    Returns:
        Optional[Tenant]: 租户对象，不存在则返回 None
    """
    query = db.query(Tenant).filter(Tenant.name == name)
    
    if not include_deleted:
        query = query.filter(Tenant.is_deleted == False)
    
    return query.first()


def get_tenants_paginated(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    include_deleted: bool = False,
    only_active: bool = True
) -> Tuple[List[Tenant], int]:
    """
    获取租户列表（分页）
    
    Args:
        db: 数据库会话
        skip: 跳过的记录数
        limit: 返回的最大记录数
        search: 搜索关键词（按名称搜索）
        sort_by: 排序字段
        sort_order: 排序方向 (asc/desc)
        include_deleted: 是否包含已删除的租户
        only_active: 是否只返回激活的租户
        
    Returns:
        Tuple[List[Tenant], int]: (租户列表, 总数)
    """
    query = db.query(Tenant)
    
    # 过滤已删除的租户
    if not include_deleted:
        query = query.filter(Tenant.is_deleted == False)
    
    # 过滤非激活的租户
    if only_active:
        query = query.filter(Tenant.is_active == True)
    
    # 如果提供了搜索关键词，添加搜索条件
    if search:
        query = query.filter(Tenant.name.ilike(f"%{search}%"))
    
    # 排序
    if hasattr(Tenant, sort_by):
        sort_column = getattr(Tenant, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
    else:
        # 默认按创建时间降序
        query = query.order_by(Tenant.created_at.desc())
    
    # 获取总数
    total = query.count()
    
    # 分页查询
    tenants = query.offset(skip).limit(limit).all()
    
    return tenants, total


def search_tenants(
    db: Session,
    search_term: str,
    limit: int = 10
) -> List[Tenant]:
    """
    搜索租户（简单搜索）
    
    用于搜索建议、快速搜索等场景
    
    Args:
        db: 数据库会话
        search_term: 搜索关键词
        limit: 返回的最大记录数
        
    Returns:
        List[Tenant]: 匹配的租户列表
    """
    return (
        db.query(Tenant)
        .filter(Tenant.name.ilike(f"%{search_term}%"))
        .limit(limit)
        .all()
    )


def update_tenant(
    db: Session, 
    tenant_id: int, 
    tenant_update: TenantUpdate
) -> Optional[Tenant]:
    """
    更新租户信息
    
    Args:
        db: 数据库会话
        tenant_id: 租户ID
        tenant_update: 更新数据
        
    Returns:
        Optional[Tenant]: 更新后的租户对象，不存在则返回 None
        
    Raises:
        DuplicateResourceException: 如果新名称已存在
        DatabaseException: 数据库操作失败
    """
    try:
        db_tenant = get_tenant(db, tenant_id)
        if not db_tenant:
            return None
        
        # 只更新提供的字段
        update_data = tenant_update.model_dump(exclude_unset=True)
        
        # 如果更新名称，检查是否已存在
        if "name" in update_data:
            new_name = update_data["name"]
            existing_tenant = get_tenant_by_name(db, new_name)
            if existing_tenant and existing_tenant.id != tenant_id:
                raise DuplicateResourceException(
                    resource_type="租户",
                    field="名称",
                    value=new_name
                )
        
        for field, value in update_data.items():
            setattr(db_tenant, field, value)
        
        db.commit()
        db.refresh(db_tenant)
        return db_tenant
        
    except DuplicateResourceException:
        raise
    except Exception as e:
        db.rollback()
        raise DatabaseException(f"更新租户时发生错误: {str(e)}")


def delete_tenant(db: Session, tenant_id: int) -> bool:
    """
    删除租户（硬删除）
    
    注意：这会级联删除所有关联的用户和数据
    
    Args:
        db: 数据库会话
        tenant_id: 租户ID
        
    Returns:
        bool: 删除成功返回 True，租户不存在返回 False
    """
    db_tenant = get_tenant(db, tenant_id)
    if not db_tenant:
        return False
    
    db.delete(db_tenant)
    db.commit()
    return True


def soft_delete_tenant(db: Session, tenant_id: int) -> Optional[Tenant]:
    """
    软删除租户（标记为删除）
    
    Args:
        db: 数据库会话
        tenant_id: 租户ID
        
    Returns:
        Optional[Tenant]: 软删除后的租户对象，不存在则返回 None
    """
    db_tenant = get_tenant(db, tenant_id)
    if not db_tenant:
        return None
    
    db_tenant.soft_delete()
    db.commit()
    db.refresh(db_tenant)
    
    return db_tenant


def activate_tenant(db: Session, tenant_id: int) -> Optional[Tenant]:
    """
    激活租户
    
    Args:
        db: 数据库会话
        tenant_id: 租户ID
        
    Returns:
        Optional[Tenant]: 激活后的租户对象，不存在则返回 None
    """
    db_tenant = get_tenant(db, tenant_id)
    if not db_tenant:
        return None
    
    db_tenant.activate()
    db.commit()
    db.refresh(db_tenant)
    
    return db_tenant


def deactivate_tenant(db: Session, tenant_id: int) -> Optional[Tenant]:
    """
    停用租户
    
    Args:
        db: 数据库会话
        tenant_id: 租户ID
        
    Returns:
        Optional[Tenant]: 停用后的租户对象，不存在则返回 None
    """
    db_tenant = get_tenant(db, tenant_id)
    if not db_tenant:
        return None
    
    db_tenant.deactivate()
    db.commit()
    db.refresh(db_tenant)
    
    return db_tenant


def restore_tenant(db: Session, tenant_id: int) -> Optional[Tenant]:
    """
    恢复软删除的租户
    
    Args:
        db: 数据库会话
        tenant_id: 租户ID
        
    Returns:
        Optional[Tenant]: 恢复后的租户对象，不存在则返回 None
    """
    db_tenant = get_tenant(db, tenant_id, include_deleted=True)
    if not db_tenant or not db_tenant.is_deleted:
        return None
    
    db_tenant.restore()
    db.commit()
    db.refresh(db_tenant)
    
    return db_tenant


def get_tenant_user_count(db: Session, tenant_id: int) -> int:
    """
    获取租户下的用户数量
    
    Args:
        db: 数据库会话
        tenant_id: 租户ID
        
    Returns:
        int: 用户数量
    """
    db_tenant = get_tenant(db, tenant_id)
    if not db_tenant:
        return 0
    
    # 注意：User 模型尚未完全配置，暂时返回 0
    # return db_tenant.users.count()
    return 0


def get_tenant_stats(db: Session, tenant_id: int) -> dict:
    """
    获取租户统计信息
    
    Args:
        db: 数据库会话
        tenant_id: 租户ID
        
    Returns:
        dict: 包含统计信息的字典
    """
    db_tenant = get_tenant(db, tenant_id)
    if not db_tenant:
        return {}
    
    return {
        "id": db_tenant.id,
        "name": db_tenant.name,
        "user_count": 0,  # 注意：User 模型尚未完全配置，暂时返回 0
        "created_at": db_tenant.created_at,
        "updated_at": db_tenant.updated_at
    }


def tenant_exists(db: Session, tenant_id: int) -> bool:
    """
    检查租户是否存在
    
    Args:
        db: 数据库会话
        tenant_id: 租户ID
        
    Returns:
        bool: 存在返回 True，否则返回 False
    """
    return db.query(Tenant).filter(Tenant.id == tenant_id).count() > 0


def tenant_name_exists(db: Session, name: str, exclude_id: Optional[int] = None) -> bool:
    """
    检查租户名称是否存在
    
    Args:
        db: 数据库会话
        name: 租户名称
        exclude_id: 排除的租户ID（用于更新时检查）
        
    Returns:
        bool: 存在返回 True，否则返回 False
    """
    query = db.query(Tenant).filter(Tenant.name == name)
    
    if exclude_id:
        query = query.filter(Tenant.id != exclude_id)
    
    return query.count() > 0


def bulk_create_tenants(db: Session, tenants_data: List[TenantCreate]) -> Tuple[List[Tenant], List[dict]]:
    """
    批量创建租户
    
    Args:
        db: 数据库会话
        tenants_data: 租户创建数据列表
        
    Returns:
        Tuple[List[Tenant], List[dict]]: (成功创建的租户列表, 失败信息列表)
    """
    success_tenants = []
    failed_results = []
    
    for tenant_data in tenants_data:
        try:
            # 检查名称是否已存在
            if tenant_name_exists(db, tenant_data.name):
                failed_results.append({
                    "tenant": tenant_data,
                    "error": f"租户名称 '{tenant_data.name}' 已存在"
                })
                continue
            
            # 创建租户
            tenant = create_tenant(db, tenant_data)
            success_tenants.append(tenant)
            
        except Exception as e:
            failed_results.append({
                "tenant": tenant_data,
                "error": str(e)
            })
    
    return success_tenants, failed_results