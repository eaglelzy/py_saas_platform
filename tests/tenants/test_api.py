"""
租户 API 单元测试

测试租户管理相关的所有 API 端点，包括：
- 租户的 CRUD 操作
- 租户状态管理
- 租户统计信息
- 批量操作
- 数据验证
- 异常处理
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from unittest.mock import patch, MagicMock
from typing import List

from src.saas.tenants.schemas import (
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    TenantListResponse,
    TenantStats,
    TenantBulkCreate,
    TenantBulkResponse
)
from src.core.exceptions import (
    BusinessLogicException,
    ResourceNotFoundException,
    DuplicateResourceException,
    DatabaseException
)


class TestCreateTenant:
    """测试创建租户 API"""

    def test_create_tenant_success(self, client: TestClient, db: Session):
        """测试成功创建租户"""
        tenant_data = {"name": "测试租户"}
        response = client.post("/api/v1/tenants/", json=tenant_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "测试租户"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_tenant_duplicate_name(self, client: TestClient, db: Session):
        """测试创建重复名称的租户"""
        # 先创建一个租户
        tenant_data = {"name": "重复租户"}
        client.post("/api/v1/tenants/", json=tenant_data)
        
        # 再次创建相同名称的租户
        response = client.post("/api/v1/tenants/", json=tenant_data)
        assert response.status_code == 409  # 更新为409状态码
        data = response.json()
        assert "租户 名称 '重复租户' 已存在" in data["detail"]

    def test_create_tenant_validation_errors(self, client: TestClient, db: Session):
        """测试创建租户的数据验证错误"""
        # 测试空名称
        response = client.post("/api/v1/tenants/", json={"name": ""})
        assert response.status_code == 422
        
        # 测试包含特殊字符的名称
        response = client.post("/api/v1/tenants/", json={"name": "测试@公司"})
        assert response.status_code == 422
        
        # 测试包含空格的名称
        response = client.post("/api/v1/tenants/", json={"name": "测试 公司"})
        assert response.status_code == 422
        
        # 测试名称过长
        response = client.post("/api/v1/tenants/", json={"name": "a" * 101})
        assert response.status_code == 422
        
        # 测试缺少必填字段
        response = client.post("/api/v1/tenants/", json={})
        assert response.status_code == 422

    def test_create_tenant_valid_names(self, client: TestClient, db: Session):
        """测试有效的租户名称"""
        valid_names = [
            "测试租户",
            "TestTenant",
            "测试_Tenant",
            "ABC公司",
            "测试公司_ABC",
            "测试租户123",
            "TestTenant2024",
            "ABC公司_2024"
        ]
        
        for name in valid_names:
            response = client.post("/api/v1/tenants/", json={"name": name})
            assert response.status_code == 201
            assert response.json()["name"] == name

    @patch('src.saas.tenants.crud.create_tenant')
    def test_create_tenant_database_exception(self, mock_create_tenant, client: TestClient, db: Session):
        """测试创建租户时数据库异常"""
        # 模拟数据库异常
        mock_create_tenant.side_effect = DatabaseException("数据库连接失败")
        
        tenant_data = {"name": "测试租户"}
        response = client.post("/api/v1/tenants/", json=tenant_data)
        
        assert response.status_code == 400  # API层包装为BusinessLogicException
        data = response.json()
        assert "创建租户失败: 数据库连接失败" in data["detail"]

    @patch('src.saas.tenants.crud.create_tenant')
    def test_create_tenant_integrity_error(self, mock_create_tenant, client: TestClient, db: Session):
        """测试创建租户时完整性错误"""
        # 模拟完整性错误
        mock_create_tenant.side_effect = IntegrityError("statement", "params", "orig")
        
        tenant_data = {"name": "测试租户"}
        response = client.post("/api/v1/tenants/", json=tenant_data)
        
        assert response.status_code == 400  # API层包装为BusinessLogicException
        data = response.json()
        assert "创建租户失败" in data["detail"]

    @patch('src.saas.tenants.crud.create_tenant')
    def test_create_tenant_general_exception(self, mock_create_tenant, client: TestClient, db: Session):
        """测试创建租户时一般异常"""
        # 模拟一般异常
        mock_create_tenant.side_effect = Exception("未知错误")
        
        tenant_data = {"name": "测试租户"}
        response = client.post("/api/v1/tenants/", json=tenant_data)
        
        assert response.status_code == 400  # API层包装为BusinessLogicException
        data = response.json()
        assert "创建租户失败: 未知错误" in data["detail"]


class TestGetTenant:
    """测试获取单个租户 API"""

    def test_get_tenant_success(self, client: TestClient, db: Session):
        """测试成功获取租户"""
        # 先创建一个租户
        tenant_data = {"name": "测试租户"}
        create_response = client.post("/api/v1/tenants/", json=tenant_data)
        tenant_id = create_response.json()["id"]
        
        # 获取租户
        response = client.get(f"/api/v1/tenants/{tenant_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == tenant_id
        assert data["name"] == "测试租户"

    def test_get_tenant_not_found(self, client: TestClient, db: Session):
        """测试获取不存在的租户"""
        response = client.get("/api/v1/tenants/99999")
        assert response.status_code == 404
        data = response.json()
        assert "租户 (ID: 99999) 不存在" in data["detail"]

    def test_get_tenant_include_deleted(self, client: TestClient, db: Session):
        """测试获取已删除的租户"""
        # 先创建一个租户
        tenant_data = {"name": "待删除租户"}
        create_response = client.post("/api/v1/tenants/", json=tenant_data)
        tenant_id = create_response.json()["id"]
        
        # 软删除租户
        client.patch(f"/api/v1/tenants/{tenant_id}/soft-delete")
        
        # 不包含已删除的租户
        response = client.get(f"/api/v1/tenants/{tenant_id}")
        assert response.status_code == 404
        data = response.json()
        assert f"租户 (ID: {tenant_id}) 不存在" in data["detail"]
        
        # 包含已删除的租户
        response = client.get(f"/api/v1/tenants/{tenant_id}?include_deleted=true")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "待删除租户"


class TestGetTenants:
    """测试获取租户列表 API"""

    def test_get_tenants_success(self, client: TestClient, db: Session):
        """测试成功获取租户列表"""
        # 创建几个测试租户
        tenant_names = ["测试租户1", "测试租户2", "测试租户3"]
        for name in tenant_names:
            client.post("/api/v1/tenants/", json={"name": name})
        
        response = client.get("/api/v1/tenants/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert len(data["items"]) >= 3

    def test_get_tenants_pagination(self, client: TestClient, db: Session):
        """测试分页功能"""
        # 创建多个租户
        tenant_names = ["分页测试1", "分页测试2", "分页测试3", "分页测试4", "分页测试5"]
        for name in tenant_names:
            client.post("/api/v1/tenants/", json={"name": name})
        
        # 测试第一页
        response = client.get("/api/v1/tenants?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        
        # 测试第二页
        response = client.get("/api/v1/tenants?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 2

    def test_get_tenants_search(self, client: TestClient, db: Session):
        """测试搜索功能"""
        # 创建测试租户
        client.post("/api/v1/tenants/", json={"name": "搜索测试租户"})
        client.post("/api/v1/tenants/", json={"name": "其他租户"})
        
        # 搜索包含"搜索"的租户
        response = client.get("/api/v1/tenants?search=搜索")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any("搜索" in item["name"] for item in data["items"])

    def test_get_tenants_sorting(self, client: TestClient, db: Session):
        """测试排序功能"""
        # 创建测试租户
        client.post("/api/v1/tenants/", json={"name": "C租户"})
        client.post("/api/v1/tenants/", json={"name": "A租户"})
        client.post("/api/v1/tenants/", json={"name": "B租户"})
        
        # 按名称升序排序
        response = client.get("/api/v1/tenants?sort_by=name&sort_order=asc")
        assert response.status_code == 200
        data = response.json()
        names = [item["name"] for item in data["items"]]
        assert names == sorted(names)

    def test_get_tenants_query_validation(self, client: TestClient, db: Session):
        """测试查询参数验证"""
        # 测试 limit 超出范围
        response = client.get("/api/v1/tenants?limit=200")
        assert response.status_code == 422
        
        # 测试 skip 为负数
        response = client.get("/api/v1/tenants?skip=-1")
        assert response.status_code == 422
        
        # 测试 limit 为 0
        response = client.get("/api/v1/tenants?limit=0")
        assert response.status_code == 422


class TestUpdateTenant:
    """测试更新租户 API"""

    def test_update_tenant_success(self, client: TestClient, db: Session):
        """测试成功更新租户"""
        # 先创建一个租户
        tenant_data = {"name": "原始租户"}
        create_response = client.post("/api/v1/tenants/", json=tenant_data)
        tenant_id = create_response.json()["id"]
        
        # 更新租户
        update_data = {"name": "更新后租户"}
        response = client.put(f"/api/v1/tenants/{tenant_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新后租户"

    def test_update_tenant_not_found(self, client: TestClient, db: Session):
        """测试更新不存在的租户"""
        update_data = {"name": "更新租户"}
        response = client.put("/api/v1/tenants/99999", json=update_data)
        assert response.status_code == 400  # API层包装为BusinessLogicException
        data = response.json()
        assert "更新租户失败: 租户 (ID: 99999) 不存在" in data["detail"]

    def test_update_tenant_duplicate_name(self, client: TestClient, db: Session):
        """测试更新为重复名称"""
        # 创建两个租户
        client.post("/api/v1/tenants/", json={"name": "租户A"})
        create_response = client.post("/api/v1/tenants/", json={"name": "租户B"})
        tenant_id = create_response.json()["id"]
        
        # 尝试将租户B更新为租户A的名称
        update_data = {"name": "租户A"}
        response = client.put(f"/api/v1/tenants/{tenant_id}", json=update_data)
        assert response.status_code == 409  # 更新为409状态码
        data = response.json()
        assert "租户 名称 '租户A' 已存在" in data["detail"]

    def test_update_tenant_validation_errors(self, client: TestClient, db: Session):
        """测试更新租户的数据验证错误"""
        # 先创建一个租户
        tenant_data = {"name": "测试租户"}
        create_response = client.post("/api/v1/tenants/", json=tenant_data)
        tenant_id = create_response.json()["id"]
        
        # 测试包含特殊字符的名称
        response = client.put(f"/api/v1/tenants/{tenant_id}", json={"name": "测试@公司"})
        assert response.status_code == 422

    @patch('src.saas.tenants.crud.update_tenant')
    def test_update_tenant_database_exception(self, mock_update_tenant, client: TestClient, db: Session):
        """测试更新租户时数据库异常"""
        # 先创建一个租户
        tenant_data = {"name": "测试租户"}
        create_response = client.post("/api/v1/tenants/", json=tenant_data)
        tenant_id = create_response.json()["id"]
        
        # 模拟数据库异常
        mock_update_tenant.side_effect = DatabaseException("数据库连接失败")
        
        update_data = {"name": "更新租户"}
        response = client.put(f"/api/v1/tenants/{tenant_id}", json=update_data)
        
        assert response.status_code == 400  # API层包装为BusinessLogicException
        data = response.json()
        assert "更新租户失败: 数据库连接失败" in data["detail"]

    @patch('src.saas.tenants.crud.update_tenant')
    def test_update_tenant_general_exception(self, mock_update_tenant, client: TestClient, db: Session):
        """测试更新租户时一般异常"""
        # 先创建一个租户
        tenant_data = {"name": "测试租户"}
        create_response = client.post("/api/v1/tenants/", json=tenant_data)
        tenant_id = create_response.json()["id"]
        
        # 模拟一般异常
        mock_update_tenant.side_effect = Exception("未知错误")
        
        update_data = {"name": "更新租户"}
        response = client.put(f"/api/v1/tenants/{tenant_id}", json=update_data)
        
        assert response.status_code == 400  # API层包装为BusinessLogicException
        data = response.json()
        assert "更新租户失败: 未知错误" in data["detail"]


class TestDeleteTenant:
    """测试删除租户 API"""

    def test_delete_tenant_success(self, client: TestClient, db: Session):
        """测试成功删除租户"""
        # 先创建一个租户
        tenant_data = {"name": "待删除租户"}
        create_response = client.post("/api/v1/tenants/", json=tenant_data)
        tenant_id = create_response.json()["id"]
        
        # 删除租户
        response = client.delete(f"/api/v1/tenants/{tenant_id}")
        assert response.status_code == 204
        
        # 验证租户已被删除
        get_response = client.get(f"/api/v1/tenants/{tenant_id}")
        assert get_response.status_code == 404

    def test_delete_tenant_not_found(self, client: TestClient, db: Session):
        """测试删除不存在的租户"""
        response = client.delete("/api/v1/tenants/99999")
        assert response.status_code == 404
        data = response.json()
        assert "租户 (ID: 99999) 不存在" in data["detail"]


class TestSearchTenants:
    """测试搜索租户 API"""

    def test_search_tenants_success(self, client: TestClient, db: Session):
        """测试成功搜索租户"""
        # 创建测试租户
        client.post("/api/v1/tenants/", json={"name": "搜索测试租户"})
        client.post("/api/v1/tenants/", json={"name": "其他租户"})
        
        # 搜索租户
        response = client.get("/api/v1/tenants/search/?q=搜索")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any("搜索" in item["name"] for item in data)

    def test_search_tenants_empty_result(self, client: TestClient, db: Session):
        """测试搜索无结果"""
        response = client.get("/api/v1/tenants/search/?q=不存在的租户")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_search_tenants_validation(self, client: TestClient, db: Session):
        """测试搜索参数验证"""
        # 测试缺少搜索关键词
        response = client.get("/api/v1/tenants/search/")
        assert response.status_code == 422
        
        # 测试 limit 超出范围
        response = client.get("/api/v1/tenants/search/?q=测试&limit=200")
        assert response.status_code == 422


class TestTenantStats:
    """测试租户统计 API"""

    def test_get_tenant_stats_success(self, client: TestClient, db: Session):
        """测试成功获取租户统计"""
        # 先创建一个租户
        tenant_data = {"name": "统计测试租户"}
        create_response = client.post("/api/v1/tenants/", json=tenant_data)
        tenant_id = create_response.json()["id"]
        
        # 获取统计信息
        response = client.get(f"/api/v1/tenants/{tenant_id}/stats")
        assert response.status_code == 200
        data = response.json()
        assert "user_count" in data
        assert data["user_count"] >= 0

    def test_get_tenant_stats_not_found(self, client: TestClient, db: Session):
        """测试获取不存在租户的统计"""
        response = client.get("/api/v1/tenants/99999/stats")
        assert response.status_code == 404
        data = response.json()
        assert "租户 (ID: 99999) 不存在" in data["detail"]


class TestBulkOperations:
    """测试批量操作 API"""

    def test_bulk_create_tenants_success(self, client: TestClient, db: Session):
        """测试成功批量创建租户"""
        bulk_data = {
            "tenants": [
                {"name": "批量租户1"},
                {"name": "批量租户2"},
                {"name": "批量租户3"}
            ]
        }
        
        response = client.post("/api/v1/tenants/bulk", json=bulk_data)
        assert response.status_code == 200
        data = response.json()
        assert "success_count" in data
        assert "failed_count" in data
        assert "success_tenants" in data
        assert "failed_results" in data
        assert data["success_count"] == 3

    def test_bulk_create_tenants_validation(self, client: TestClient, db: Session):
        """测试批量创建租户的数据验证"""
        # 测试空列表
        bulk_data = {"tenants": []}
        response = client.post("/api/v1/tenants/bulk", json=bulk_data)
        assert response.status_code == 422
        
        # 测试超出最大数量
        bulk_data = {
            "tenants": [{"name": f"租户{i}"} for i in range(101)]
        }
        response = client.post("/api/v1/tenants/bulk", json=bulk_data)
        assert response.status_code == 422

    def test_bulk_create_tenants_partial_success(self, client: TestClient, db: Session):
        """测试批量创建部分成功"""
        # 先创建一个租户
        client.post("/api/v1/tenants/", json={"name": "重复租户"})
        
        # 批量创建包含重复名称的租户
        bulk_data = {
            "tenants": [
                {"name": "新租户1"},
                {"name": "重复租户"},  # 重复名称
                {"name": "新租户2"}
            ]
        }
        
        response = client.post("/api/v1/tenants/bulk", json=bulk_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 2
        assert data["failed_count"] == 1


class TestGetTenantByName:
    """测试根据名称获取租户 API"""

    def test_get_tenant_by_name_success(self, client: TestClient, db: Session):
        """测试成功根据名称获取租户"""
        # 先创建一个租户
        tenant_data = {"name": "名称测试租户"}
        client.post("/api/v1/tenants/", json=tenant_data)
        
        # 根据名称获取租户
        response = client.get("/api/v1/tenants/name/名称测试租户")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "名称测试租户"

    def test_get_tenant_by_name_not_found(self, client: TestClient, db: Session):
        """测试根据名称获取不存在的租户"""
        response = client.get("/api/v1/tenants/name/不存在的租户")
        assert response.status_code == 404
        data = response.json()
        assert "租户 (名称: 不存在的租户) 不存在" in data["detail"]


class TestGetTenantUserCount:
    """测试获取租户用户数量 API"""

    def test_get_tenant_user_count_success(self, client: TestClient, db: Session):
        """测试成功获取租户用户数量"""
        # 先创建一个租户
        tenant_data = {"name": "用户数量测试租户"}
        create_response = client.post("/api/v1/tenants/", json=tenant_data)
        tenant_id = create_response.json()["id"]
        
        # 获取用户数量
        response = client.get(f"/api/v1/tenants/{tenant_id}/users/count")
        assert response.status_code == 200
        data = response.json()
        assert "user_count" in data
        assert data["user_count"] == 0  # 新租户没有用户

    def test_get_tenant_user_count_not_found(self, client: TestClient, db: Session):
        """测试获取不存在租户的用户数量"""
        response = client.get("/api/v1/tenants/99999/users/count")
        assert response.status_code == 404
        data = response.json()
        assert "租户 (ID: 99999) 不存在" in data["detail"]




class TestTenantStatusManagement:
    """测试租户状态管理 API"""

    def test_activate_tenant_success(self, client: TestClient, db: Session):
        """测试成功激活租户"""
        # 先创建一个租户
        tenant_data = {"name": "状态测试租户"}
        create_response = client.post("/api/v1/tenants/", json=tenant_data)
        tenant_id = create_response.json()["id"]
        
        # 激活租户
        response = client.patch(f"/api/v1/tenants/{tenant_id}/activate")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "状态测试租户"

    def test_deactivate_tenant_success(self, client: TestClient, db: Session):
        """测试成功停用租户"""
        # 先创建一个租户
        tenant_data = {"name": "停用测试租户"}
        create_response = client.post("/api/v1/tenants/", json=tenant_data)
        tenant_id = create_response.json()["id"]
        
        # 停用租户
        response = client.patch(f"/api/v1/tenants/{tenant_id}/deactivate")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "停用测试租户"

    def test_soft_delete_tenant_success(self, client: TestClient, db: Session):
        """测试成功软删除租户"""
        # 先创建一个租户
        tenant_data = {"name": "软删除测试租户"}
        create_response = client.post("/api/v1/tenants/", json=tenant_data)
        tenant_id = create_response.json()["id"]
        
        # 软删除租户
        response = client.patch(f"/api/v1/tenants/{tenant_id}/soft-delete")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "软删除测试租户"

    def test_restore_tenant_success(self, client: TestClient, db: Session):
        """测试成功恢复租户"""
        # 先创建一个租户并软删除
        tenant_data = {"name": "恢复测试租户"}
        create_response = client.post("/api/v1/tenants/", json=tenant_data)
        tenant_id = create_response.json()["id"]
        client.patch(f"/api/v1/tenants/{tenant_id}/soft-delete")
        
        # 恢复租户
        response = client.patch(f"/api/v1/tenants/{tenant_id}/restore")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "恢复测试租户"

    def test_status_management_not_found(self, client: TestClient, db: Session):
        """测试对不存在租户进行状态管理"""
        # 激活不存在的租户
        response = client.patch("/api/v1/tenants/99999/activate")
        assert response.status_code == 404
        data = response.json()
        assert "租户 (ID: 99999) 不存在" in data["detail"]
        
        # 停用不存在的租户
        response = client.patch("/api/v1/tenants/99999/deactivate")
        assert response.status_code == 404
        data = response.json()
        assert "租户 (ID: 99999) 不存在" in data["detail"]
        
        # 软删除不存在的租户
        response = client.patch("/api/v1/tenants/99999/soft-delete")
        assert response.status_code == 404
        data = response.json()
        assert "租户 (ID: 99999) 不存在" in data["detail"]
        
        # 恢复不存在的租户
        response = client.patch("/api/v1/tenants/99999/restore")
        assert response.status_code == 404
        data = response.json()
        assert "租户 (ID: 99999) 不存在" in data["detail"]
