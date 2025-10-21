"""
用户管理CRUD操作的单元测试

测试用户相关的数据库操作功能。
"""

import pytest
from sqlalchemy.orm import Session
from src.saas.users.crud import (
    create_user, get_user, get_user_by_email, get_users_paginated,
    update_user, delete_user, soft_delete_user, restore_user,
    activate_user, deactivate_user, update_last_login, get_user_stats,
    user_exists, email_exists, bulk_create_users, authenticate_user
)
from src.saas.users.schemas import UserCreate, UserUpdate
from src.saas.users.user import User
from src.saas.tenants.tanant import Tenant
from src.core.exceptions import DuplicateResourceException, ResourceNotFoundException


class TestCreateUser:
    """测试创建用户功能"""

    def test_create_user_success(self, db: Session):
        """测试成功创建用户"""
        # 创建租户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        # 创建用户
        user_data = UserCreate(
            name="测试用户",
            email="test@example.com",
            password="password123",
            tenant_id=tenant.id
        )
        
        user = create_user(db, user_data)
        
        assert user.name == "测试用户"
        assert user.email == "test@example.com"
        assert user.tenant_id == tenant.id
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.password != "password123"  # 密码应该被加密

    def test_create_user_duplicate_email(self, db: Session):
        """测试创建重复邮箱的用户"""
        # 创建租户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        # 创建第一个用户
        user_data1 = UserCreate(
            name="用户1",
            email="test@example.com",
            password="password123",
            tenant_id=tenant.id
        )
        create_user(db, user_data1)

        # 尝试创建相同邮箱的用户
        user_data2 = UserCreate(
            name="用户2",
            email="test@example.com",
            password="password456",
            tenant_id=tenant.id
        )
        
        with pytest.raises(DuplicateResourceException):
            create_user(db, user_data2)


class TestGetUser:
    """测试获取用户功能"""

    def test_get_user_success(self, db: Session):
        """测试成功获取用户"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = UserCreate(
            name="测试用户",
            email="test@example.com",
            password="password123",
            tenant_id=tenant.id
        )
        created_user = create_user(db, user_data)

        # 获取用户
        user = get_user(db, created_user.id)
        
        assert user is not None
        assert user.name == "测试用户"
        assert user.email == "test@example.com"

    def test_get_user_not_found(self, db: Session):
        """测试获取不存在的用户"""
        user = get_user(db, 999)
        assert user is None

    def test_get_user_by_email_success(self, db: Session):
        """测试根据邮箱获取用户"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = UserCreate(
            name="测试用户",
            email="test@example.com",
            password="password123",
            tenant_id=tenant.id
        )
        create_user(db, user_data)

        # 根据邮箱获取用户
        user = get_user_by_email(db, "test@example.com")
        
        assert user is not None
        assert user.email == "test@example.com"

    def test_get_user_by_email_not_found(self, db: Session):
        """测试获取不存在的邮箱用户"""
        user = get_user_by_email(db, "nonexistent@example.com")
        assert user is None


class TestGetUsersPaginated:
    """测试分页获取用户功能"""

    def test_get_users_paginated_success(self, db: Session):
        """测试成功获取用户列表"""
        # 创建租户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        # 创建多个用户
        for i in range(5):
            user_data = UserCreate(
                name=f"用户{i+1}",
                email=f"user{i+1}@example.com",
                password="password123",
                tenant_id=tenant.id
            )
            create_user(db, user_data)

        # 获取用户列表
        users, total = get_users_paginated(db, skip=0, limit=3)
        
        assert len(users) == 3
        assert total == 5

    def test_get_users_paginated_with_search(self, db: Session):
        """测试带搜索的用户列表"""
        # 创建租户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        # 创建用户
        user_data1 = UserCreate(
            name="张三",
            email="zhangsan@example.com",
            password="password123",
            tenant_id=tenant.id
        )
        user_data2 = UserCreate(
            name="李四",
            email="lisi@example.com",
            password="password123",
            tenant_id=tenant.id
        )
        create_user(db, user_data1)
        create_user(db, user_data2)

        # 搜索用户
        users, total = get_users_paginated(db, search="张三")
        
        assert len(users) == 1
        assert users[0].name == "张三"


class TestUpdateUser:
    """测试更新用户功能"""

    def test_update_user_success(self, db: Session):
        """测试成功更新用户"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = UserCreate(
            name="测试用户",
            email="test@example.com",
            password="password123",
            tenant_id=tenant.id
        )
        created_user = create_user(db, user_data)

        # 更新用户
        update_data = UserUpdate(
            name="更新用户",
            email="updated@example.com"
        )
        updated_user = update_user(db, created_user.id, update_data)
        
        assert updated_user.name == "更新用户"
        assert updated_user.email == "updated@example.com"

    def test_update_user_not_found(self, db: Session):
        """测试更新不存在的用户"""
        update_data = UserUpdate(name="更新用户")
        result = update_user(db, 999, update_data)
        assert result is None


class TestDeleteUser:
    """测试删除用户功能"""

    def test_delete_user_success(self, db: Session):
        """测试成功删除用户"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = UserCreate(
            name="测试用户",
            email="test@example.com",
            password="password123",
            tenant_id=tenant.id
        )
        created_user = create_user(db, user_data)

        # 删除用户
        success = delete_user(db, created_user.id)
        assert success is True

        # 验证用户已被删除
        user = get_user(db, created_user.id)
        assert user is None

    def test_delete_user_not_found(self, db: Session):
        """测试删除不存在的用户"""
        success = delete_user(db, 999)
        assert success is False


class TestSoftDeleteUser:
    """测试软删除用户功能"""

    def test_soft_delete_user_success(self, db: Session):
        """测试成功软删除用户"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = UserCreate(
            name="测试用户",
            email="test@example.com",
            password="password123",
            tenant_id=tenant.id
        )
        created_user = create_user(db, user_data)

        # 软删除用户
        success = soft_delete_user(db, created_user.id)
        assert success is True

        # 验证用户已被软删除
        user = get_user(db, created_user.id)
        assert user is None

        # 验证用户在包含已删除的查询中存在
        user_deleted = get_user(db, created_user.id, include_deleted=True)
        assert user_deleted is not None
        assert user_deleted.is_deleted is True

    def test_restore_user_success(self, db: Session):
        """测试成功恢复用户"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = UserCreate(
            name="测试用户",
            email="test@example.com",
            password="password123",
            tenant_id=tenant.id
        )
        created_user = create_user(db, user_data)

        # 软删除用户
        soft_delete_user(db, created_user.id)

        # 恢复用户
        success = restore_user(db, created_user.id)
        assert success is True

        # 验证用户已恢复
        user = get_user(db, created_user.id)
        assert user is not None
        assert user.is_deleted is False


class TestUserStatusManagement:
    """测试用户状态管理功能"""

    def test_activate_user_success(self, db: Session):
        """测试成功激活用户"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = UserCreate(
            name="测试用户",
            email="test@example.com",
            password="password123",
            tenant_id=tenant.id,
            is_active=False
        )
        created_user = create_user(db, user_data)

        # 激活用户
        success = activate_user(db, created_user.id)
        assert success is True

        # 验证用户已激活
        user = get_user(db, created_user.id)
        assert user.is_active is True

    def test_deactivate_user_success(self, db: Session):
        """测试成功停用用户"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = UserCreate(
            name="测试用户",
            email="test@example.com",
            password="password123",
            tenant_id=tenant.id
        )
        created_user = create_user(db, user_data)

        # 停用用户
        success = deactivate_user(db, created_user.id)
        assert success is True

        # 验证用户已停用
        user = get_user(db, created_user.id)
        assert user.is_active is False


class TestUserStats:
    """测试用户统计功能"""

    def test_get_user_stats_success(self, db: Session):
        """测试成功获取用户统计"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = UserCreate(
            name="测试用户",
            email="test@example.com",
            password="password123",
            tenant_id=tenant.id
        )
        created_user = create_user(db, user_data)

        # 获取用户统计
        stats = get_user_stats(db, created_user.id)
        
        assert stats["id"] == created_user.id
        assert stats["name"] == "测试用户"
        assert stats["email"] == "test@example.com"
        assert stats["tenant_name"] == "测试租户"

    def test_get_user_stats_not_found(self, db: Session):
        """测试获取不存在用户的统计"""
        stats = get_user_stats(db, 999)
        assert stats == {}


class TestUserValidation:
    """测试用户验证功能"""

    def test_user_exists_success(self, db: Session):
        """测试用户存在验证"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = UserCreate(
            name="测试用户",
            email="test@example.com",
            password="password123",
            tenant_id=tenant.id
        )
        created_user = create_user(db, user_data)

        # 验证用户存在
        exists = user_exists(db, created_user.id)
        assert exists is True

    def test_user_exists_not_found(self, db: Session):
        """测试用户不存在验证"""
        exists = user_exists(db, 999)
        assert exists is False

    def test_email_exists_success(self, db: Session):
        """测试邮箱存在验证"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = UserCreate(
            name="测试用户",
            email="test@example.com",
            password="password123",
            tenant_id=tenant.id
        )
        create_user(db, user_data)

        # 验证邮箱存在
        exists = email_exists(db, "test@example.com")
        assert exists is True

    def test_email_exists_not_found(self, db: Session):
        """测试邮箱不存在验证"""
        exists = email_exists(db, "nonexistent@example.com")
        assert exists is False


class TestBulkOperations:
    """测试批量操作功能"""

    def test_bulk_create_users_success(self, db: Session):
        """测试成功批量创建用户"""
        # 创建租户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        # 批量创建用户
        users_data = [
            UserCreate(
                name=f"用户{i+1}",
                email=f"user{i+1}@example.com",
                password="password123",
                tenant_id=tenant.id
            )
            for i in range(3)
        ]
        
        result = bulk_create_users(db, users_data)
        
        assert result["success_count"] == 3
        assert result["failed_count"] == 0
        assert len(result["errors"]) == 0

    def test_bulk_create_users_with_errors(self, db: Session):
        """测试批量创建用户时的错误处理"""
        # 创建租户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        # 创建第一个用户
        user_data1 = UserCreate(
            name="用户1",
            email="test@example.com",
            password="password123",
            tenant_id=tenant.id
        )
        create_user(db, user_data1)

        # 批量创建用户（包含重复邮箱）
        users_data = [
            UserCreate(
                name="用户2",
                email="test@example.com",  # 重复邮箱
                password="password123",
                tenant_id=tenant.id
            ),
            UserCreate(
                name="用户3",
                email="user3@example.com",
                password="password123",
                tenant_id=tenant.id
            )
        ]
        
        result = bulk_create_users(db, users_data)
        
        assert result["success_count"] == 1
        assert result["failed_count"] == 1
        assert len(result["errors"]) == 1


class TestUserAuthentication:
    """测试用户认证功能"""

    def test_authenticate_user_success(self, db: Session):
        """测试成功用户认证"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = UserCreate(
            name="测试用户",
            email="test@example.com",
            password="password123",
            tenant_id=tenant.id
        )
        create_user(db, user_data)

        # 认证用户
        user = authenticate_user(db, "test@example.com", "password123")
        
        assert user is not None
        assert user.email == "test@example.com"

    def test_authenticate_user_wrong_password(self, db: Session):
        """测试错误密码认证"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = UserCreate(
            name="测试用户",
            email="test@example.com",
            password="password123",
            tenant_id=tenant.id
        )
        create_user(db, user_data)

        # 使用错误密码认证
        user = authenticate_user(db, "test@example.com", "wrongpassword")
        assert user is None

    def test_authenticate_user_inactive(self, db: Session):
        """测试停用用户认证"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = UserCreate(
            name="测试用户",
            email="test@example.com",
            password="password123",
            tenant_id=tenant.id,
            is_active=False
        )
        create_user(db, user_data)

        # 认证停用用户
        user = authenticate_user(db, "test@example.com", "password123")
        assert user is None
