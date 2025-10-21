"""
租户 CRUD 操作单元测试

测试租户的创建、读取、更新、删除等数据库操作。
"""

import pytest
from sqlalchemy.orm import Session

from src.saas.tenants.crud import (
    create_tenant,
    get_tenant,
    get_tenant_by_name,
    get_tenants_paginated,
    search_tenants,
    update_tenant,
    delete_tenant,
    soft_delete_tenant,
    restore_tenant,
    activate_tenant,
    deactivate_tenant,
    get_tenant_user_count,
    get_tenant_stats,
    tenant_exists,
    tenant_name_exists,
    bulk_create_tenants
)
from src.saas.tenants.schemas import TenantCreate, TenantUpdate
from src.saas.tenants.tanant import Tenant
from pydantic import ValidationError


class TestCreateTenant:
    """测试创建租户功能"""
    
    def test_create_tenant_success(self, db: Session):
        """测试成功创建租户"""
        tenant_data = TenantCreate(name="测试租户")
        tenant = create_tenant(db, tenant_data)
        
        assert tenant.id is not None
        assert tenant.name == "测试租户"
        assert tenant.is_active is True
        assert tenant.is_deleted is False
        assert tenant.created_at is not None
        assert tenant.updated_at is not None
        assert tenant.deleted_at is None
    
    def test_create_tenant_duplicate_name(self, db: Session):
        """测试创建重复名称的租户"""
        # 先创建一个租户
        tenant_data = TenantCreate(name="重复名称租户")
        create_tenant(db, tenant_data)
        
        # 尝试创建同名租户
        duplicate_data = TenantCreate(name="重复名称租户")
        with pytest.raises(ValueError, match="租户名称 '重复名称租户' 已存在"):
            create_tenant(db, duplicate_data)
    
    def test_create_tenant_empty_name(self, db: Session):
        """测试创建空名称的租户"""
        with pytest.raises(ValueError, match="String should have at least 1 character"):
            tenant_data = TenantCreate(name="")
            create_tenant(db, tenant_data)
    


class TestGetTenant:
    """测试获取租户功能"""
    
    def test_get_tenant_success(self, db: Session, test_tenant: Tenant):
        """测试成功获取租户"""
        tenant = get_tenant(db, test_tenant.id)
        
        assert tenant is not None
        assert tenant.id == test_tenant.id
        assert tenant.name == test_tenant.name
    
    def test_get_tenant_not_found(self, db: Session):
        """测试获取不存在的租户"""
        tenant = get_tenant(db, 99999)
        assert tenant is None
    
    def test_get_tenant_include_deleted(self, db: Session, test_tenant: Tenant):
        """测试获取已删除的租户"""
        # 软删除租户
        test_tenant.soft_delete()
        db.commit()
        
        # 不包含已删除的租户
        tenant = get_tenant(db, test_tenant.id, include_deleted=False)
        assert tenant is None
        
        # 包含已删除的租户
        tenant = get_tenant(db, test_tenant.id, include_deleted=True)
        assert tenant is not None
        assert tenant.is_deleted is True


class TestGetTenantByName:
    """测试根据名称获取租户功能"""
    
    def test_get_tenant_by_name_success(self, db: Session, test_tenant: Tenant):
        """测试成功根据名称获取租户"""
        tenant = get_tenant_by_name(db, test_tenant.name)
        
        assert tenant is not None
        assert tenant.name == test_tenant.name
    
    def test_get_tenant_by_name_not_found(self, db: Session):
        """测试获取不存在的租户名称"""
        tenant = get_tenant_by_name(db, "不存在的租户")
        assert tenant is None


class TestGetTenantsPaginated:
    """测试分页获取租户列表功能"""
    
    def test_get_tenants_paginated_success(self, db: Session, test_tenants: list[Tenant]):
        """测试成功获取租户列表"""
        tenants, total = get_tenants_paginated(db, skip=0, limit=10)
        
        assert len(tenants) == len(test_tenants)
        assert total == len(test_tenants)
    
    def test_get_tenants_paginated_pagination(self, db: Session, test_tenants: list[Tenant]):
        """测试分页功能"""
        # 第一页
        tenants, total = get_tenants_paginated(db, skip=0, limit=2)
        assert len(tenants) == 2
        assert total == len(test_tenants)
        
        # 第二页
        tenants, total = get_tenants_paginated(db, skip=2, limit=2)
        assert len(tenants) == 2
        assert total == len(test_tenants)
    
    def test_get_tenants_paginated_search(self, db: Session, test_tenants: list[Tenant]):
        """测试搜索功能"""
        tenants, total = get_tenants_paginated(db, search="测试")
        
        assert total >= 0
        for tenant in tenants:
            assert "测试" in tenant.name
    
    def test_get_tenants_paginated_sorting(self, db: Session, test_tenants: list[Tenant]):
        """测试排序功能"""
        # 按名称升序
        tenants, total = get_tenants_paginated(db, sort_by="name", sort_order="asc")
        assert tenants[0].name <= tenants[1].name
        
        # 按创建时间降序
        tenants, total = get_tenants_paginated(db, sort_by="created_at", sort_order="desc")
        assert tenants[0].created_at >= tenants[1].created_at
    
    def test_get_tenants_paginated_filters(self, db: Session, test_tenant: Tenant):
        """测试过滤功能"""
        # 只获取激活的租户
        tenants, total = get_tenants_paginated(db, only_active=True)
        for tenant in tenants:
            assert tenant.is_active is True
        
        # 包含已删除的租户
        test_tenant.soft_delete()
        db.commit()
        
        tenants, total = get_tenants_paginated(db, include_deleted=True)
        deleted_tenants = [t for t in tenants if t.is_deleted]
        assert len(deleted_tenants) > 0


class TestSearchTenants:
    """测试搜索租户功能"""
    
    def test_search_tenants_success(self, db: Session, test_tenants: list[Tenant]):
        """测试成功搜索租户"""
        tenants = search_tenants(db, "测试", limit=5)
        
        assert len(tenants) <= 5
        for tenant in tenants:
            assert "测试" in tenant.name
    
    def test_search_tenants_no_results(self, db: Session):
        """测试搜索无结果"""
        tenants = search_tenants(db, "不存在的关键词")
        assert len(tenants) == 0


class TestUpdateTenant:
    """测试更新租户功能"""
    
    def test_update_tenant_success(self, db: Session, test_tenant: Tenant):
        """测试成功更新租户"""
        update_data = TenantUpdate(name="更新后的租户名称")
        updated_tenant = update_tenant(db, test_tenant.id, update_data)
        
        assert updated_tenant is not None
        assert updated_tenant.name == "更新后的租户名称"
        assert updated_tenant.id == test_tenant.id
    
    def test_update_tenant_not_found(self, db: Session):
        """测试更新不存在的租户"""
        update_data = TenantUpdate(name="新名称")
        result = update_tenant(db, 99999, update_data)
        assert result is None
    
    def test_update_tenant_duplicate_name(self, db: Session, test_tenants: list[Tenant]):
        """测试更新为重复名称"""
        tenant1, tenant2 = test_tenants[0], test_tenants[1]
        update_data = TenantUpdate(name=tenant2.name)
        
        with pytest.raises(ValueError, match="租户名称"):
            update_tenant(db, tenant1.id, update_data)
    
    def test_update_tenant_partial_update(self, db: Session, test_tenant: Tenant):
        """测试部分更新"""
        original_name = test_tenant.name
        update_data = TenantUpdate()  # 空更新
        
        updated_tenant = update_tenant(db, test_tenant.id, update_data)
        
        assert updated_tenant is not None
        assert updated_tenant.name == original_name  # 名称未改变


class TestDeleteTenant:
    """测试删除租户功能"""
    
    def test_delete_tenant_success(self, db: Session, test_tenant: Tenant):
        """测试成功删除租户"""
        result = delete_tenant(db, test_tenant.id)
        
        assert result is True
        # 验证租户已被删除
        tenant = get_tenant(db, test_tenant.id)
        assert tenant is None
    
    def test_delete_tenant_not_found(self, db: Session):
        """测试删除不存在的租户"""
        result = delete_tenant(db, 99999)
        assert result is False


class TestSoftDeleteTenant:
    """测试软删除租户功能"""
    
    def test_soft_delete_tenant_success(self, db: Session, test_tenant: Tenant):
        """测试成功软删除租户"""
        result = soft_delete_tenant(db, test_tenant.id)
        
        assert result is not None
        assert result.is_deleted is True
        assert result.deleted_at is not None
    
    def test_soft_delete_tenant_not_found(self, db: Session):
        """测试软删除不存在的租户"""
        result = soft_delete_tenant(db, 99999)
        assert result is None


class TestRestoreTenant:
    """测试恢复租户功能"""
    
    def test_restore_tenant_success(self, db: Session, test_tenant: Tenant):
        """测试成功恢复租户"""
        # 先软删除
        test_tenant.soft_delete()
        db.commit()
        
        # 恢复租户
        result = restore_tenant(db, test_tenant.id)
        
        assert result is not None
        assert result.is_deleted is False
        assert result.deleted_at is None
    
    def test_restore_tenant_not_deleted(self, db: Session, test_tenant: Tenant):
        """测试恢复未删除的租户"""
        result = restore_tenant(db, test_tenant.id)
        assert result is None


class TestActivateDeactivateTenant:
    """测试激活/停用租户功能"""
    
    def test_activate_tenant_success(self, db: Session, test_tenant: Tenant):
        """测试成功激活租户"""
        # 先停用
        test_tenant.deactivate()
        db.commit()
        
        # 激活
        result = activate_tenant(db, test_tenant.id)
        
        assert result is not None
        assert result.is_active is True
    
    def test_deactivate_tenant_success(self, db: Session, test_tenant: Tenant):
        """测试成功停用租户"""
        result = deactivate_tenant(db, test_tenant.id)
        
        assert result is not None
        assert result.is_active is False


class TestTenantStats:
    """测试租户统计功能"""
    
    def test_get_tenant_user_count(self, db: Session, test_tenant: Tenant):
        """测试获取租户用户数量"""
        count = get_tenant_user_count(db, test_tenant.id)
        assert count >= 0
    
    def test_get_tenant_stats(self, db: Session, test_tenant: Tenant):
        """测试获取租户统计信息"""
        stats = get_tenant_stats(db, test_tenant.id)
        
        assert "id" in stats
        assert "name" in stats
        assert "user_count" in stats
        assert "created_at" in stats
        assert "updated_at" in stats


class TestTenantValidation:
    """测试租户验证功能"""
    
    def test_tenant_exists(self, db: Session, test_tenant: Tenant):
        """测试租户是否存在"""
        assert tenant_exists(db, test_tenant.id) is True
        assert tenant_exists(db, 99999) is False
    
    def test_tenant_name_exists(self, db: Session, test_tenant: Tenant):
        """测试租户名称是否存在"""
        assert tenant_name_exists(db, test_tenant.name) is True
        assert tenant_name_exists(db, "不存在的名称") is False
        
        # 测试排除特定ID的情况
        assert tenant_name_exists(db, test_tenant.name, exclude_id=test_tenant.id) is False


class TestBulkCreateTenants:
    """测试批量创建租户功能"""
    
    def test_bulk_create_tenants_success(self, db: Session):
        """测试成功批量创建租户"""
        tenants_data = [
            TenantCreate(name="批量租户1"),
            TenantCreate(name="批量租户2"),
            TenantCreate(name="批量租户3")
        ]
        
        success_tenants, failed_results = bulk_create_tenants(db, tenants_data)
        
        assert len(success_tenants) == 3
        assert len(failed_results) == 0
    
    def test_bulk_create_tenants_partial_success(self, db: Session):
        """测试部分成功的批量创建"""
        # 先创建一个租户
        create_tenant(db, TenantCreate(name="重复租户"))
        
        tenants_data = [
            TenantCreate(name="新租户1"),
            TenantCreate(name="重复租户"),  # 重复名称
            TenantCreate(name="新租户2")
        ]
        
        success_tenants, failed_results = bulk_create_tenants(db, tenants_data)
        
        assert len(success_tenants) == 2
        assert len(failed_results) == 1
        assert "重复租户" in failed_results[0]["error"]


class TestTenantBusinessLogic:
    """测试租户业务逻辑"""
    
    def test_tenant_availability(self, db: Session, test_tenant: Tenant):
        """测试租户可用性"""
        # 正常租户
        assert test_tenant.is_available() is True
        
        # 停用租户
        test_tenant.deactivate()
        assert test_tenant.is_available() is False
        
        # 软删除租户
        test_tenant.activate()
        test_tenant.soft_delete()
        assert test_tenant.is_available() is False
    
    def test_tenant_status_display(self, db: Session, test_tenant: Tenant):
        """测试租户状态显示"""
        # 正常状态
        assert test_tenant.get_status_display() == "正常"
        
        # 停用状态
        test_tenant.deactivate()
        assert test_tenant.get_status_display() == "已停用"
        
        # 删除状态
        test_tenant.soft_delete()
        assert test_tenant.get_status_display() == "已删除"
    
    def test_tenant_deleted_display(self, db: Session, test_tenant: Tenant):
        """测试删除时间显示"""
        # 未删除
        assert test_tenant.get_deleted_display() == "未删除"
        
        # 已删除
        test_tenant.soft_delete()
        deleted_display = test_tenant.get_deleted_display()
        assert deleted_display != "未删除"
        assert isinstance(deleted_display, str)


class TestTenantValidation:
    """测试租户数据校验功能"""
    
    def test_tenant_create_valid_names(self):
        """测试有效的租户创建名称"""
        valid_names = [
            "ABC教育公司",
            "ABC_Education", 
            "教育_公司",
            "Test_Company",
            "A",
            "中",
            "ABC_教育公司",
            "Education_教育"
        ]
        
        for name in valid_names:
            tenant = TenantCreate(name=name)
            assert tenant.name == name
    
    def test_tenant_create_invalid_names(self):
        """测试无效的租户创建名称"""
        invalid_names = [
            "",                    # 空字符串
            "   ",                 # 只有空格
            "ABC123",              # 包含数字
            "ABC-教育",            # 包含连字符
            "ABC.教育",            # 包含点号
            "ABC 教育",            # 包含空格
            "ABC@教育",            # 包含特殊字符
            "ABC<>教育",           # 包含HTML标签
            "ABC&教育",            # 包含特殊字符
        ]
        
        for name in invalid_names:
            with pytest.raises(ValidationError):
                TenantCreate(name=name)
    
    def test_tenant_create_name_length_validation(self):
        """测试租户创建名称长度校验"""
        # 测试名称过长
        long_name = "A" * 101  # 超过100个字符
        with pytest.raises(ValidationError):
            TenantCreate(name=long_name)
    
    def test_tenant_update_valid_names(self):
        """测试有效的租户更新名称"""
        valid_names = [
            "ABC教育公司",
            "ABC_Education", 
            "教育_公司",
            "Test_Company"
        ]
        
        for name in valid_names:
            tenant = TenantUpdate(name=name)
            assert tenant.name == name
    
    def test_tenant_update_invalid_names(self):
        """测试无效的租户更新名称"""
        invalid_names = [
            "",                    # 空字符串
            "   ",                 # 只有空格
            "ABC123",              # 包含数字
            "ABC-教育",            # 包含连字符
            "ABC.教育",            # 包含点号
            "ABC 教育",            # 包含空格
            "ABC@教育",            # 包含特殊字符
        ]
        
        for name in invalid_names:
            with pytest.raises(ValidationError):
                TenantUpdate(name=name)
    
    def test_tenant_update_none_name(self):
        """测试租户更新时名称为 None"""
        tenant = TenantUpdate(name=None)
        assert tenant.name is None
    
    def test_tenant_update_name_length_validation(self):
        """测试租户更新名称长度校验"""
        # 测试名称过长
        long_name = "A" * 101  # 超过100个字符
        with pytest.raises(ValidationError):
            TenantUpdate(name=long_name)
    
    def test_tenant_create_validation_error_messages(self):
        """测试租户创建校验错误信息"""
        # 测试空名称错误信息
        with pytest.raises(ValidationError) as exc_info:
            TenantCreate(name="")
        assert "String should have at least 1 character" in str(exc_info.value)
        
        # 测试包含非法字符错误信息
        with pytest.raises(ValidationError) as exc_info:
            TenantCreate(name="ABC123")
        assert "租户名称只能包含中文字符、英文字母和下划线" in str(exc_info.value)
        
        # 测试只有空格错误信息
        with pytest.raises(ValidationError) as exc_info:
            TenantCreate(name="   ")
        assert "租户名称不能为空" in str(exc_info.value)
    
    def test_tenant_update_validation_error_messages(self):
        """测试租户更新校验错误信息"""
        # 测试包含非法字符错误信息
        with pytest.raises(ValidationError) as exc_info:
            TenantUpdate(name="ABC123")
        assert "租户名称只能包含中文字符、英文字母和下划线" in str(exc_info.value)
        
        # 测试只有空格错误信息
        with pytest.raises(ValidationError) as exc_info:
            TenantUpdate(name="   ")
        assert "租户名称不能为空" in str(exc_info.value)