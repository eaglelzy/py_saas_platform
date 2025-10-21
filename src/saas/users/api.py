"""
用户管理的API接口

提供用户相关的RESTful API端点，包括CRUD操作、搜索、状态管理等。
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.core.db import get_db
from . import crud
from .schemas import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    UserPasswordChange, UserActivate, UserDeactivate, UserStats,
    UserSearchParams, UserBulkCreate, UserBulkResponse,
    UserLogin, UserLoginResponse
)
from src.core.exceptions import (
    BusinessLogicException,
    ResourceNotFoundException,
    DuplicateResourceException,
    ValidationException
)

router = APIRouter(tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    创建新用户
    
    Args:
        user: 用户创建数据
        db: 数据库会话
        
    Returns:
        UserResponse: 创建的用户信息
        
    Raises:
        409: 邮箱已存在
        400: 数据验证失败
        500: 服务器内部错误
    """
    try:
        return crud.create_user(db, user)
    except DuplicateResourceException as e:
        raise e
    except Exception as e:
        raise BusinessLogicException(f"创建用户失败: {str(e)}")


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, include_deleted: bool = Query(False, description="是否包含已删除的用户"), db: Session = Depends(get_db)):
    """
    根据ID获取用户
    
    Args:
        user_id: 用户ID
        include_deleted: 是否包含已删除的用户
        db: 数据库会话
        
    Returns:
        UserResponse: 用户信息
        
    Raises:
        404: 用户不存在
    """
    user = crud.get_user(db, user_id, include_deleted=include_deleted)
    if not user:
        raise ResourceNotFoundException(resource_type="用户", resource_id=user_id)
    return user


@router.get("/", response_model=UserListResponse)
def get_users(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    only_active: bool = Query(True, description="只显示激活的用户"),
    include_deleted: bool = Query(False, description="是否包含已删除的用户"),
    tenant_id: Optional[int] = Query(None, description="租户ID筛选"),
    db: Session = Depends(get_db)
):
    """
    获取用户列表（分页）
    
    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        search: 搜索关键词
        sort_by: 排序字段
        sort_order: 排序方向
        only_active: 只显示激活的用户
        include_deleted: 是否包含已删除的用户
        tenant_id: 租户ID筛选
        db: 数据库会话
        
    Returns:
        UserListResponse: 用户列表和分页信息
    """
    users, total = crud.get_users_paginated(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        only_active=only_active,
        include_deleted=include_deleted,
        tenant_id=tenant_id
    )
    
    return UserListResponse(
        items=users,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit
    )


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    """
    更新用户信息
    
    Args:
        user_id: 用户ID
        user_update: 用户更新数据
        db: 数据库会话
        
    Returns:
        UserResponse: 更新后的用户信息
        
    Raises:
        404: 用户不存在
        409: 邮箱已存在
        400: 数据验证失败
    """
    try:
        updated_user = crud.update_user(db, user_id, user_update)
        if not updated_user:
            raise ResourceNotFoundException(resource_type="用户", resource_id=user_id)
        return updated_user
    except (DuplicateResourceException, ResourceNotFoundException) as e:
        raise e
    except Exception as e:
        raise BusinessLogicException(f"更新用户失败: {str(e)}")


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    物理删除用户
    
    Args:
        user_id: 用户ID
        db: 数据库会话
        
    Raises:
        404: 用户不存在
    """
    success = crud.delete_user(db, user_id)
    if not success:
        raise ResourceNotFoundException(resource_type="用户", resource_id=user_id)


@router.patch("/{user_id}/soft-delete", status_code=status.HTTP_204_NO_CONTENT)
def soft_delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    软删除用户
    
    Args:
        user_id: 用户ID
        db: 数据库会话
        
    Raises:
        404: 用户不存在
    """
    success = crud.soft_delete_user(db, user_id)
    if not success:
        raise ResourceNotFoundException(resource_type="用户", resource_id=user_id)


@router.patch("/{user_id}/restore", status_code=status.HTTP_204_NO_CONTENT)
def restore_user(user_id: int, db: Session = Depends(get_db)):
    """
    恢复已删除的用户
    
    Args:
        user_id: 用户ID
        db: 数据库会话
        
    Raises:
        404: 用户不存在或未删除
    """
    success = crud.restore_user(db, user_id)
    if not success:
        raise ResourceNotFoundException(resource_type="用户", resource_id=user_id)


@router.patch("/{user_id}/activate", response_model=UserActivate)
def activate_user(user_id: int, db: Session = Depends(get_db)):
    """
    激活用户
    
    Args:
        user_id: 用户ID
        db: 数据库会话
        
    Returns:
        UserActivate: 激活操作响应
        
    Raises:
        404: 用户不存在
    """
    success = crud.activate_user(db, user_id)
    if not success:
        raise ResourceNotFoundException(resource_type="用户", resource_id=user_id)
    
    user = crud.get_user(db, user_id)
    return UserActivate(
        id=user.id,
        name=user.name,
        is_active=user.is_active,
        message="用户已激活"
    )


@router.patch("/{user_id}/deactivate", response_model=UserDeactivate)
def deactivate_user(user_id: int, db: Session = Depends(get_db)):
    """
    停用用户
    
    Args:
        user_id: 用户ID
        db: 数据库会话
        
    Returns:
        UserDeactivate: 停用操作响应
        
    Raises:
        404: 用户不存在
    """
    success = crud.deactivate_user(db, user_id)
    if not success:
        raise ResourceNotFoundException(resource_type="用户", resource_id=user_id)
    
    user = crud.get_user(db, user_id)
    return UserDeactivate(
        id=user.id,
        name=user.name,
        is_active=user.is_active,
        message="用户已停用"
    )


@router.get("/{user_id}/stats", response_model=UserStats)
def get_user_stats(user_id: int, db: Session = Depends(get_db)):
    """
    获取用户统计信息
    
    Args:
        user_id: 用户ID
        db: 数据库会话
        
    Returns:
        UserStats: 用户统计信息
        
    Raises:
        404: 用户不存在
    """
    stats = crud.get_user_stats(db, user_id)
    if not stats:
        raise ResourceNotFoundException(resource_type="用户", resource_id=user_id)
    
    return UserStats(**stats)


@router.post("/search", response_model=UserListResponse)
def search_users(
    search_params: UserSearchParams,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数"),
    db: Session = Depends(get_db)
):
    """
    搜索用户
    
    Args:
        search_params: 搜索参数
        skip: 跳过的记录数
        limit: 返回的记录数
        db: 数据库会话
        
    Returns:
        UserListResponse: 搜索结果
    """
    users, total = crud.search_users(
        db=db,
        search_params=search_params.model_dump(exclude_none=True),
        skip=skip,
        limit=limit
    )
    
    return UserListResponse(
        items=users,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit
    )


@router.post("/bulk", response_model=UserBulkResponse)
def bulk_create_users(users_data: UserBulkCreate, db: Session = Depends(get_db)):
    """
    批量创建用户
    
    Args:
        users_data: 批量用户数据
        db: 数据库会话
        
    Returns:
        UserBulkResponse: 批量创建结果
    """
    result = crud.bulk_create_users(db, users_data.users)
    return UserBulkResponse(**result)


@router.get("/email/{email}", response_model=UserResponse)
def get_user_by_email(email: str, include_deleted: bool = Query(False, description="是否包含已删除的用户"), db: Session = Depends(get_db)):
    """
    根据邮箱获取用户
    
    Args:
        email: 用户邮箱
        include_deleted: 是否包含已删除的用户
        db: 数据库会话
        
    Returns:
        UserResponse: 用户信息
        
    Raises:
        404: 用户不存在
    """
    user = crud.get_user_by_email(db, email, include_deleted=include_deleted)
    if not user:
        raise ResourceNotFoundException(resource_type="用户", resource_field="邮箱", resource_value=email)
    return user


@router.post("/{user_id}/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(user_id: int, password_data: UserPasswordChange, db: Session = Depends(get_db)):
    """
    修改用户密码
    
    Args:
        user_id: 用户ID
        password_data: 密码修改数据
        db: 数据库会话
        
    Raises:
        404: 用户不存在
        400: 当前密码错误
    """
    user = crud.get_user(db, user_id)
    if not user:
        raise ResourceNotFoundException(resource_type="用户", resource_id=user_id)
    
    # 验证当前密码
    if not crud.verify_password(password_data.current_password, user.password):
        raise ValidationException("当前密码错误")
    
    # 更新密码
    user.password = crud.get_password_hash(password_data.new_password)
    db.commit()


@router.post("/login", response_model=UserLoginResponse)
def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录
    
    Args:
        login_data: 登录数据
        db: 数据库会话
        
    Returns:
        UserLoginResponse: 登录响应（包含访问令牌）
        
    Raises:
        401: 认证失败
    """
    user = crud.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误"
        )
    
    # 更新最后登录时间
    crud.update_last_login(db, user.id)
    
    # TODO: 生成JWT令牌
    # 这里暂时返回一个模拟的令牌
    access_token = "mock_jwt_token_here"
    
    return UserLoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user,
        expires_in=3600  # 1小时
    )


@router.get("/{user_id}/validate", response_model=dict)
def validate_user(user_id: int, db: Session = Depends(get_db)):
    """
    验证用户是否存在
    
    Args:
        user_id: 用户ID
        db: 数据库会话
        
    Returns:
        dict: 验证结果
    """
    exists = crud.user_exists(db, user_id)
    return {
        "user_id": user_id,
        "exists": exists,
        "message": "用户存在" if exists else "用户不存在"
    }


@router.get("/email/{email}/validate", response_model=dict)
def validate_email(email: str, db: Session = Depends(get_db)):
    """
    验证邮箱是否已存在
    
    Args:
        email: 邮箱地址
        db: 数据库会话
        
    Returns:
        dict: 验证结果
    """
    exists = crud.email_exists(db, email)
    return {
        "email": email,
        "exists": exists,
        "message": "邮箱已存在" if exists else "邮箱可用"
    }
