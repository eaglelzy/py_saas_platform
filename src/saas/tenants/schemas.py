"""
租户（Tenant）Pydantic Schemas

定义用于 API 请求验证和响应序列化的数据模型。
"""

import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class TenantBase(BaseModel):
    """租户基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="租户名称")


class TenantCreate(TenantBase):
    """
    创建租户的请求模型
    
    用于 POST /api/v1/tenants 端点
    """
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """自定义名称校验 - 只允许中英文和下划线"""
        if not v or not v.strip():
            raise ValueError('租户名称不能为空')
        
        # 去除首尾空格
        v = v.strip()
        
        # 检查长度
        if len(v) < 1:
            raise ValueError('租户名称至少需要1个字符')
        
        if len(v) > 100:
            raise ValueError('租户名称不能超过100个字符')
        
        # 检查是否只包含中文、英文、数字和下划线
        # 正则表达式：^[\u4e00-\u9fa5a-zA-Z0-9_]+$
        # \u4e00-\u9fa5: 中文字符范围
        # a-zA-Z: 英文字母
        # 0-9: 数字
        # _: 下划线
        if not re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9_]+$', v):
            raise ValueError('租户名称只能包含中文字符、英文字母、数字和下划线')
        
        return v


class TenantUpdate(BaseModel):
    """
    更新租户的请求模型
    
    用于 PUT /api/v1/tenants/{tenant_id} 端点
    所有字段都是可选的，只更新提供的字段
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="租户名称")
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """自定义名称校验 - 只允许中英文和下划线"""
        if v is None:
            return v
        
        if not v or not v.strip():
            raise ValueError('租户名称不能为空')
        
        # 去除首尾空格
        v = v.strip()
        
        # 检查长度
        if len(v) < 1:
            raise ValueError('租户名称至少需要1个字符')
        
        if len(v) > 100:
            raise ValueError('租户名称不能超过100个字符')
        
        # 检查是否只包含中文、英文、数字和下划线
        if not re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9_]+$', v):
            raise ValueError('租户名称只能包含中文字符、英文字母、数字和下划线')
        
        return v


class TenantResponse(TenantBase):
    """
    租户响应模型
    
    用于所有返回单个租户信息的端点
    """
    id: int = Field(..., description="租户唯一标识符")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)


class TenantListResponse(BaseModel):
    """
    租户列表响应模型
    
    用于 GET /api/v1/tenants 端点，支持分页
    """
    total: int = Field(..., description="租户总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    items: list[TenantResponse] = Field(..., description="租户列表")


class TenantActivate(BaseModel):
    """租户激活操作响应"""
    id: int
    name: str
    is_active: bool = True
    message: str = "租户已激活"


class TenantDeactivate(BaseModel):
    """租户停用操作响应"""
    id: int
    name: str
    is_active: bool = False
    message: str = "租户已停用"


class TenantStats(BaseModel):
    """租户统计信息响应"""
    id: int
    name: str
    user_count: int = Field(..., description="用户数量")
    created_at: datetime = Field(..., description="创建时间")
    last_activity: Optional[datetime] = Field(None, description="最后活动时间")


class TenantSearchParams(BaseModel):
    """租户搜索参数"""
    search: Optional[str] = Field(None, description="搜索关键词")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")
    sort_by: Optional[str] = Field("created_at", description="排序字段")
    sort_order: Optional[str] = Field("desc", description="排序方向")


class TenantBulkCreate(BaseModel):
    """批量创建租户请求模型"""
    tenants: list[TenantCreate] = Field(..., min_length=1, max_length=100, description="租户列表")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "tenants": [
                    {"name": "租户A"},
                    {"name": "租户B"},
                    {"name": "租户C"}
                ]
            }
        }
    }


class TenantBulkResponse(BaseModel):
    """批量操作响应模型"""
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    success_tenants: list[TenantResponse] = Field(..., description="成功创建的租户")
    failed_results: list[dict] = Field(..., description="失败的结果详情")