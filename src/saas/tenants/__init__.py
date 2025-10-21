"""
租户模块

提供租户管理的完整功能，包括：
- 数据模型 (models)
- 业务逻辑 (crud)
- API 接口 (api)
- 数据验证 (schemas)
"""

from .api import router
from .crud import *
from .schemas import *
from .tanant import Tenant

__all__ = [
    "router",
    "Tenant",
    # CRUD functions
    "create_tenant",
    "get_tenant",
    "get_tenant_by_name",
    "get_tenants_paginated",
    "search_tenants",
    "update_tenant",
    "delete_tenant",
    "soft_delete_tenant",
    "restore_tenant",
    "activate_tenant",
    "deactivate_tenant",
    "get_tenant_user_count",
    "get_tenant_stats",
    "tenant_exists",
    "tenant_name_exists",
    "bulk_create_tenants",
    # Schemas
    "TenantBase",
    "TenantCreate",
    "TenantUpdate",
    "TenantResponse",
    "TenantListResponse",
    "TenantActivate",
    "TenantDeactivate",
    "TenantStats",
    "TenantSearchParams",
    "TenantBulkCreate",
    "TenantBulkResponse"
]
