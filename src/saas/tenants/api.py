"""
租户 API 端点

提供租户管理的 RESTful API 接口，包括：
- 租户的 CRUD 操作
- 租户状态管理
- 租户统计信息
- 批量操作
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.saas.tenants import crud, schemas
from src.saas.tenants.schemas import (
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    TenantListResponse,
    TenantActivate,
    TenantDeactivate,
    TenantStats,
    TenantSearchParams,
    TenantBulkCreate,
    TenantBulkResponse
)

# 创建路由器
router = APIRouter(prefix="/tenants", tags=["tenants"])

@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
def create_tenant(
    tenant: TenantCreate,
    db: Session = Depends(get_db)
):
    """
    创建新租户
    
    Args:
        tenant: 租户创建数据
        db: 数据库会话
        
    Returns:
        TenantResponse: 创建的租户信息
        
    Raises:
        HTTPException: 400 - 租户名称已存在
        HTTPException: 422 - 数据验证失败
    """
    try:
        return crud.create_tenant(db, tenant)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(
    tenant_id: int,
    include_deleted: bool = Query(False, description="是否包含已删除的租户"),
    db: Session = Depends(get_db)
):
    """
    根据 ID 获取租户信息
    
    Args:
        tenant_id: 租户 ID
        include_deleted: 是否包含已删除的租户
        db: 数据库会话
        
    Returns:
        TenantResponse: 租户信息
        
    Raises:
        HTTPException: 404 - 租户不存在
    """
    tenant = crud.get_tenant(db, tenant_id, include_deleted=include_deleted)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"租户 ID {tenant_id} 不存在"
        )
    return tenant


@router.get("/", response_model=TenantListResponse)
def get_tenants(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    only_active: bool = Query(True, description="只显示激活的租户"),
    include_deleted: bool = Query(False, description="是否包含已删除的租户"),
    db: Session = Depends(get_db)
):
    """
    获取租户列表（分页）
    
    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        search: 搜索关键词
        sort_by: 排序字段
        sort_order: 排序方向
        only_active: 只显示激活的租户
        include_deleted: 是否包含已删除的租户
        db: 数据库会话
        
    Returns:
        TenantListResponse: 租户列表和总数
    """
    tenants, total = crud.get_tenants_paginated(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        only_active=only_active,
        include_deleted=include_deleted
    )
    
    return TenantListResponse(
        items=tenants,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit
    )


@router.get("/search/", response_model=List[TenantResponse])
def search_tenants(
    q: str = Query(..., description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50, description="返回的记录数"),
    db: Session = Depends(get_db)
):
    """
    搜索租户
    
    Args:
        q: 搜索关键词
        limit: 返回的记录数
        db: 数据库会话
        
    Returns:
        List[TenantResponse]: 匹配的租户列表
    """
    return crud.search_tenants(db, q, limit=limit)


@router.put("/{tenant_id}", response_model=TenantResponse)
def update_tenant(
    tenant_id: int,
    tenant_update: TenantUpdate,
    db: Session = Depends(get_db)
):
    """
    更新租户信息
    
    Args:
        tenant_id: 租户 ID
        tenant_update: 租户更新数据
        db: 数据库会话
        
    Returns:
        TenantResponse: 更新后的租户信息
        
    Raises:
        HTTPException: 404 - 租户不存在
        HTTPException: 400 - 租户名称已存在
    """
    try:
        updated_tenant = crud.update_tenant(db, tenant_id, tenant_update)
        if not updated_tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"租户 ID {tenant_id} 不存在"
            )
        return updated_tenant
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tenant(
    tenant_id: int,
    db: Session = Depends(get_db)
):
    """
    删除租户（硬删除）
    
    Args:
        tenant_id: 租户 ID
        db: 数据库会话
        
    Raises:
        HTTPException: 404 - 租户不存在
    """
    success = crud.delete_tenant(db, tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"租户 ID {tenant_id} 不存在"
        )


@router.patch("/{tenant_id}/soft-delete", response_model=TenantResponse)
def soft_delete_tenant(
    tenant_id: int,
    db: Session = Depends(get_db)
):
    """
    软删除租户
    
    Args:
        tenant_id: 租户 ID
        db: 数据库会话
        
    Returns:
        TenantResponse: 软删除后的租户信息
        
    Raises:
        HTTPException: 404 - 租户不存在
    """
    tenant = crud.soft_delete_tenant(db, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"租户 ID {tenant_id} 不存在"
        )
    return tenant


@router.patch("/{tenant_id}/restore", response_model=TenantResponse)
def restore_tenant(
    tenant_id: int,
    db: Session = Depends(get_db)
):
    """
    恢复软删除的租户
    
    Args:
        tenant_id: 租户 ID
        db: 数据库会话
        
    Returns:
        TenantResponse: 恢复后的租户信息
        
    Raises:
        HTTPException: 404 - 租户不存在或未删除
    """
    tenant = crud.restore_tenant(db, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"租户 ID {tenant_id} 不存在或未被删除"
        )
    return tenant


@router.patch("/{tenant_id}/activate", response_model=TenantResponse)
def activate_tenant(
    tenant_id: int,
    db: Session = Depends(get_db)
):
    """
    激活租户
    
    Args:
        tenant_id: 租户 ID
        db: 数据库会话
        
    Returns:
        TenantResponse: 激活后的租户信息
        
    Raises:
        HTTPException: 404 - 租户不存在
    """
    tenant = crud.activate_tenant(db, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"租户 ID {tenant_id} 不存在"
        )
    return tenant


@router.patch("/{tenant_id}/deactivate", response_model=TenantResponse)
def deactivate_tenant(
    tenant_id: int,
    db: Session = Depends(get_db)
):
    """
    停用租户
    
    Args:
        tenant_id: 租户 ID
        db: 数据库会话
        
    Returns:
        TenantResponse: 停用后的租户信息
        
    Raises:
        HTTPException: 404 - 租户不存在
    """
    tenant = crud.deactivate_tenant(db, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"租户 ID {tenant_id} 不存在"
        )
    return tenant


@router.get("/{tenant_id}/stats", response_model=TenantStats)
def get_tenant_stats(
    tenant_id: int,
    db: Session = Depends(get_db)
):
    """
    获取租户统计信息
    
    Args:
        tenant_id: 租户 ID
        db: 数据库会话
        
    Returns:
        TenantStats: 租户统计信息
        
    Raises:
        HTTPException: 404 - 租户不存在
    """
    # 先检查租户是否存在
    tenant = crud.get_tenant(db, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"租户 ID {tenant_id} 不存在"
        )
    
    return crud.get_tenant_stats(db, tenant_id)


@router.post("/bulk", response_model=TenantBulkResponse)
def bulk_create_tenants(
    bulk_data: TenantBulkCreate,
    db: Session = Depends(get_db)
):
    """
    批量创建租户
    
    Args:
        bulk_data: 批量创建数据
        db: 数据库会话
        
    Returns:
        TenantBulkResponse: 批量操作结果
    """
    success_tenants, failed_results = crud.bulk_create_tenants(db, bulk_data.tenants)
    
    return TenantBulkResponse(
        success_count=len(success_tenants),
        failed_count=len(failed_results),
        success_tenants=success_tenants,
        failed_results=failed_results
    )


@router.get("/name/{name}", response_model=TenantResponse)
def get_tenant_by_name(
    name: str,
    db: Session = Depends(get_db)
):
    """
    根据名称获取租户
    
    Args:
        name: 租户名称
        db: 数据库会话
        
    Returns:
        TenantResponse: 租户信息
        
    Raises:
        HTTPException: 404 - 租户不存在
    """
    tenant = crud.get_tenant_by_name(db, name)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"租户名称 '{name}' 不存在"
        )
    return tenant


@router.get("/{tenant_id}/users/count")
def get_tenant_user_count(
    tenant_id: int,
    db: Session = Depends(get_db)
):
    """
    获取租户用户数量
    
    Args:
        tenant_id: 租户 ID
        db: 数据库会话
        
    Returns:
        dict: 用户数量信息
        
    Raises:
        HTTPException: 404 - 租户不存在
    """
    # 先检查租户是否存在
    tenant = crud.get_tenant(db, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"租户 ID {tenant_id} 不存在"
        )
    
    count = crud.get_tenant_user_count(db, tenant_id)
    return {"tenant_id": tenant_id, "user_count": count}
