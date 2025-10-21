"""
用户管理API的单元测试

测试用户相关的API端点功能。
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from src.saas.users.schemas import UserCreate, UserUpdate, UserBulkCreate
from src.saas.users.user import User
from src.saas.tenants.tanant import Tenant
from src.saas.users.crud import create_user, soft_delete_user, activate_user, deactivate_user, restore_user
from src.core.exceptions import ResourceNotFoundException, DuplicateResourceException, BusinessLogicException, ValidationException


class TestCreateUser:
    """测试创建用户 API"""

    def test_create_user_success(self, client: TestClient, db: Session):
        """测试成功创建用户"""
        # 创建租户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = {
            "name": "测试用户",
            "email": "test@example.com",
            "password": "password123",
            "tenant_id": tenant.id
        }
        response = client.post("/api/v1/users", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "测试用户"
        assert data["email"] == "test@example.com"
        assert data["tenant_id"] == tenant.id
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_user_duplicate_email(self, client: TestClient, db: Session):
        """测试创建重复邮箱的用户"""
        # 创建租户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        # 创建第一个用户
        user_data1 = {
            "name": "用户1",
            "email": "test@example.com",
            "password": "password123",
            "tenant_id": tenant.id
        }
        client.post("/api/v1/users", json=user_data1)

        # 尝试创建相同邮箱的用户
        user_data2 = {
            "name": "用户2",
            "email": "test@example.com",
            "password": "password456",
            "tenant_id": tenant.id
        }
        response = client.post("/api/v1/users", json=user_data2)
        
        assert response.status_code == 409
        assert "邮箱" in response.json()["detail"]

    def test_create_user_validation_errors(self, client: TestClient, db: Session):
        """测试创建用户时的数据验证错误"""
        # 创建租户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        # 名称为空
        response = client.post("/api/v1/users", json={
            "name": "",
            "email": "test@example.com",
            "password": "password123",
            "tenant_id": tenant.id
        })
        assert response.status_code == 422

        # 密码过短
        response = client.post("/api/v1/users", json={
            "name": "测试用户",
            "email": "test@example.com",
            "password": "123",
            "tenant_id": tenant.id
        })
        assert response.status_code == 422

        # 邮箱格式错误
        response = client.post("/api/v1/users", json={
            "name": "测试用户",
            "email": "invalid-email",
            "password": "password123",
            "tenant_id": tenant.id
        })
        assert response.status_code == 422

    def test_create_user_valid_names(self, client: TestClient, db: Session):
        """测试创建用户时各种有效姓名"""
        # 创建租户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        valid_names = [
            "张三",
            "John Doe",
            "张三 李四",
            "User123",
            "测试用户 2024"
        ]
        
        for i, name in enumerate(valid_names):
            response = client.post("/api/v1/users", json={
                "name": name,
                "email": f"user{i}@example.com",
                "password": "password123",
                "tenant_id": tenant.id
            })
            assert response.status_code == 201, f"Failed for name: {name}, response: {response.json()}"
            assert response.json()["name"] == name


class TestGetUser:
    """测试获取用户 API"""

    def test_get_user_success(self, client: TestClient, db: Session):
        """测试成功获取用户"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = {
            "name": "测试用户",
            "email": "test@example.com",
            "password": "password123",
            "tenant_id": tenant.id
        }
        create_response = client.post("/api/v1/users", json=user_data)
        user_id = create_response.json()["id"]

        # 获取用户
        response = client.get(f"/api/v1/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "测试用户"
        assert data["email"] == "test@example.com"

    def test_get_user_not_found(self, client: TestClient, db: Session):
        """测试获取不存在的用户"""
        response = client.get("/api/v1/users/999")
        assert response.status_code == 404
        assert "用户" in response.json()["detail"]

    def test_get_user_include_deleted(self, client: TestClient, db: Session):
        """测试获取包含已删除的用户"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = {
            "name": "测试用户",
            "email": "test@example.com",
            "password": "password123",
            "tenant_id": tenant.id
        }
        create_response = client.post("/api/v1/users", json=user_data)
        user_id = create_response.json()["id"]

        # 软删除用户
        client.patch(f"/api/v1/users/{user_id}/soft-delete")

        # 不包含已删除用户
        response = client.get(f"/api/v1/users/{user_id}")
        assert response.status_code == 404

        # 包含已删除用户
        response = client.get(f"/api/v1/users/{user_id}?include_deleted=true")
        assert response.status_code == 200


class TestGetUsers:
    """测试获取用户列表 API"""

    def test_get_users_success(self, client: TestClient, db: Session):
        """测试成功获取用户列表"""
        # 创建租户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        # 创建多个用户
        for i in range(3):
            user_data = {
                "name": f"用户{i+1}",
                "email": f"user{i+1}@example.com",
                "password": "password123",
                "tenant_id": tenant.id
            }
            client.post("/api/v1/users", json=user_data)

        response = client.get("/api/v1/users")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert len(data["items"]) >= 3

    def test_get_users_pagination(self, client: TestClient, db: Session):
        """测试分页功能"""
        # 创建租户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        # 创建多个用户
        for i in range(5):
            user_data = {
                "name": f"分页用户{i+1}",
                "email": f"page{i+1}@example.com",
                "password": "password123",
                "tenant_id": tenant.id
            }
            client.post("/api/v1/users", json=user_data)

        # 测试第一页
        response = client.get("/api/v1/users?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2

        # 测试第二页
        response = client.get("/api/v1/users?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 2
        assert data["page_size"] == 2

    def test_get_users_search(self, client: TestClient, db: Session):
        """测试搜索功能"""
        # 创建租户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        # 创建用户
        user_data1 = {
            "name": "张三",
            "email": "zhangsan@example.com",
            "password": "password123",
            "tenant_id": tenant.id
        }
        user_data2 = {
            "name": "李四",
            "email": "lisi@example.com",
            "password": "password123",
            "tenant_id": tenant.id
        }
        client.post("/api/v1/users", json=user_data1)
        client.post("/api/v1/users", json=user_data2)

        # 搜索用户
        response = client.get("/api/v1/users?search=张三")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "张三"

    def test_get_users_tenant_filter(self, client: TestClient, db: Session):
        """测试租户筛选"""
        # 创建两个租户
        tenant1 = Tenant(name="租户1")
        tenant2 = Tenant(name="租户2")
        db.add_all([tenant1, tenant2])
        db.commit()
        db.refresh(tenant1)
        db.refresh(tenant2)

        # 为每个租户创建用户
        for tenant, i in [(tenant1, 1), (tenant2, 2)]:
            user_data = {
                "name": f"用户{i}",
                "email": f"user{i}@example.com",
                "password": "password123",
                "tenant_id": tenant.id
            }
            client.post("/api/v1/users", json=user_data)

        # 筛选租户1的用户
        response = client.get(f"/api/v1/users?tenant_id={tenant1.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["tenant_id"] == tenant1.id


class TestUpdateUser:
    """测试更新用户 API"""

    def test_update_user_success(self, client: TestClient, db: Session):
        """测试成功更新用户"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = {
            "name": "测试用户",
            "email": "test@example.com",
            "password": "password123",
            "tenant_id": tenant.id
        }
        create_response = client.post("/api/v1/users", json=user_data)
        user_id = create_response.json()["id"]

        # 更新用户
        update_data = {
            "name": "更新用户",
            "email": "updated@example.com"
        }
        response = client.put(f"/api/v1/users/{user_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新用户"
        assert data["email"] == "updated@example.com"

    def test_update_user_not_found(self, client: TestClient, db: Session):
        """测试更新不存在的用户"""
        update_data = {"name": "更新用户"}
        response = client.put("/api/v1/users/999", json=update_data)
        assert response.status_code == 404

    def test_update_user_duplicate_email(self, client: TestClient, db: Session):
        """测试更新为重复邮箱"""
        # 创建租户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        # 创建两个用户
        user_data1 = {
            "name": "用户1",
            "email": "user1@example.com",
            "password": "password123",
            "tenant_id": tenant.id
        }
        user_data2 = {
            "name": "用户2",
            "email": "user2@example.com",
            "password": "password123",
            "tenant_id": tenant.id
        }
        create_response1 = client.post("/api/v1/users", json=user_data1)
        client.post("/api/v1/users", json=user_data2)
        
        user_id1 = create_response1.json()["id"]

        # 尝试将用户1的邮箱更新为用户2的邮箱
        update_data = {"email": "user2@example.com"}
        response = client.put(f"/api/v1/users/{user_id1}", json=update_data)
        assert response.status_code == 409


class TestDeleteUser:
    """测试删除用户 API"""

    def test_delete_user_success(self, client: TestClient, db: Session):
        """测试成功删除用户"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = {
            "name": "测试用户",
            "email": "test@example.com",
            "password": "password123",
            "tenant_id": tenant.id
        }
        create_response = client.post("/api/v1/users", json=user_data)
        user_id = create_response.json()["id"]

        # 删除用户
        response = client.delete(f"/api/v1/users/{user_id}")
        assert response.status_code == 204

        # 验证用户已被删除
        response = client.get(f"/api/v1/users/{user_id}")
        assert response.status_code == 404

    def test_delete_user_not_found(self, client: TestClient, db: Session):
        """测试删除不存在的用户"""
        response = client.delete("/api/v1/users/999")
        assert response.status_code == 404


class TestUserStatusManagement:
    """测试用户状态管理 API"""

    def test_soft_delete_user_success(self, client: TestClient, db: Session):
        """测试成功软删除用户"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = {
            "name": "测试用户",
            "email": "test@example.com",
            "password": "password123",
            "tenant_id": tenant.id
        }
        create_response = client.post("/api/v1/users", json=user_data)
        user_id = create_response.json()["id"]

        # 软删除用户
        response = client.patch(f"/api/v1/users/{user_id}/soft-delete")
        assert response.status_code == 204

        # 验证用户已被软删除
        response = client.get(f"/api/v1/users/{user_id}")
        assert response.status_code == 404

    def test_restore_user_success(self, client: TestClient, db: Session):
        """测试成功恢复用户"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = {
            "name": "测试用户",
            "email": "test@example.com",
            "password": "password123",
            "tenant_id": tenant.id
        }
        create_response = client.post("/api/v1/users", json=user_data)
        user_id = create_response.json()["id"]

        # 软删除用户
        client.patch(f"/api/v1/users/{user_id}/soft-delete")

        # 恢复用户
        response = client.patch(f"/api/v1/users/{user_id}/restore")
        assert response.status_code == 204

        # 验证用户已恢复
        response = client.get(f"/api/v1/users/{user_id}")
        assert response.status_code == 200

    def test_activate_user_success(self, client: TestClient, db: Session):
        """测试成功激活用户"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = {
            "name": "测试用户",
            "email": "test@example.com",
            "password": "password123",
            "tenant_id": tenant.id,
            "is_active": False
        }
        create_response = client.post("/api/v1/users", json=user_data)
        user_id = create_response.json()["id"]

        # 激活用户
        response = client.patch(f"/api/v1/users/{user_id}/activate")
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True
        assert data["message"] == "用户已激活"

    def test_deactivate_user_success(self, client: TestClient, db: Session):
        """测试成功停用用户"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = {
            "name": "测试用户",
            "email": "test@example.com",
            "password": "password123",
            "tenant_id": tenant.id
        }
        create_response = client.post("/api/v1/users", json=user_data)
        user_id = create_response.json()["id"]

        # 停用用户
        response = client.patch(f"/api/v1/users/{user_id}/deactivate")
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        assert data["message"] == "用户已停用"


class TestUserStats:
    """测试用户统计 API"""

    def test_get_user_stats_success(self, client: TestClient, db: Session):
        """测试成功获取用户统计"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = {
            "name": "测试用户",
            "email": "test@example.com",
            "password": "password123",
            "tenant_id": tenant.id
        }
        create_response = client.post("/api/v1/users", json=user_data)
        user_id = create_response.json()["id"]

        # 获取用户统计
        response = client.get(f"/api/v1/users/{user_id}/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["name"] == "测试用户"
        assert data["email"] == "test@example.com"
        assert data["tenant_name"] == "测试租户"

    def test_get_user_stats_not_found(self, client: TestClient, db: Session):
        """测试获取不存在用户的统计"""
        response = client.get("/api/v1/users/999/stats")
        assert response.status_code == 404


class TestBulkOperations:
    """测试批量操作 API"""

    def test_bulk_create_users_success(self, client: TestClient, db: Session):
        """测试成功批量创建用户"""
        # 创建租户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        # 批量创建用户
        users_data = {
            "users": [
                {
                    "name": "用户1",
                    "email": "user1@example.com",
                    "password": "password123",
                    "tenant_id": tenant.id
                },
                {
                    "name": "用户2",
                    "email": "user2@example.com",
                    "password": "password123",
                    "tenant_id": tenant.id
                }
            ]
        }
        response = client.post("/api/v1/users/bulk", json=users_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 2
        assert data["failed_count"] == 0
        assert len(data["errors"]) == 0

    def test_bulk_create_users_with_errors(self, client: TestClient, db: Session):
        """测试批量创建用户时的错误处理"""
        # 创建租户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        # 创建第一个用户
        user_data1 = {
            "name": "用户1",
            "email": "test@example.com",
            "password": "password123",
            "tenant_id": tenant.id
        }
        client.post("/api/v1/users", json=user_data1)

        # 批量创建用户（包含重复邮箱）
        users_data = {
            "users": [
                {
                    "name": "用户2",
                    "email": "test@example.com",  # 重复邮箱
                    "password": "password123",
                    "tenant_id": tenant.id
                },
                {
                    "name": "用户3",
                    "email": "user3@example.com",
                    "password": "password123",
                    "tenant_id": tenant.id
                }
            ]
        }
        response = client.post("/api/v1/users/bulk", json=users_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 1
        assert data["failed_count"] == 1
        assert len(data["errors"]) == 1


class TestUserValidation:
    """测试用户验证 API"""

    def test_validate_user_success(self, client: TestClient, db: Session):
        """测试成功验证用户存在"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = {
            "name": "测试用户",
            "email": "test@example.com",
            "password": "password123",
            "tenant_id": tenant.id
        }
        create_response = client.post("/api/v1/users", json=user_data)
        user_id = create_response.json()["id"]

        # 验证用户存在
        response = client.get(f"/api/v1/users/{user_id}/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user_id
        assert data["exists"] is True
        assert data["message"] == "用户存在"

    def test_validate_user_not_found(self, client: TestClient, db: Session):
        """测试验证不存在的用户"""
        response = client.get("/api/v1/users/999/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == 999
        assert data["exists"] is False
        assert data["message"] == "用户不存在"

    def test_validate_email_success(self, client: TestClient, db: Session):
        """测试成功验证邮箱存在"""
        # 创建租户和用户
        tenant = Tenant(name="测试租户")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        user_data = {
            "name": "测试用户",
            "email": "test@example.com",
            "password": "password123",
            "tenant_id": tenant.id
        }
        client.post("/api/v1/users", json=user_data)

        # 验证邮箱存在
        response = client.get("/api/v1/users/email/test@example.com/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["exists"] is True
        assert data["message"] == "邮箱已存在"

    def test_validate_email_not_found(self, client: TestClient, db: Session):
        """测试验证不存在的邮箱"""
        response = client.get("/api/v1/users/email/nonexistent@example.com/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "nonexistent@example.com"
        assert data["exists"] is False
        assert data["message"] == "邮箱可用"
