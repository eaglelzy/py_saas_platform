"""
租户（Tenant）Pydantic Schemas

定义用于 API 请求验证和响应序列化的数据模型。
"""

from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional
from datetime import datetime

from src.core.validators import EmailStr, PhoneOrLandlineStr, SubdomainStr, PhoneStr, NotEmptyStr


class TenantBase(BaseModel):
    """租户基础模型 (使用 Annotated 类型)"""
    company_name: NotEmptyStr = Field(..., min_length=1, max_length=100, description="租户名称（公司或组织名称）")
    company_address: NotEmptyStr = Field(..., min_length=1, max_length=255, description="公司地址")
    company_phone: PhoneOrLandlineStr = Field(..., min_length=1, max_length=20, description="公司电话")
    company_email: EmailStr = Field(..., min_length=1, max_length=100, description="公司邮箱")
    company_website: Optional[str] = Field(None, max_length=255, description="公司网站")
    company_logo: Optional[str] = Field(None, max_length=255, description="公司Logo")
    contact_person: NotEmptyStr = Field(..., min_length=1, max_length=20, description="联系人姓名")
    contact_phone: PhoneStr = Field(..., min_length=1, max_length=20, description="联系人电话")
    subdomain: SubdomainStr = Field(..., min_length=3, max_length=100, description="子域名")


class TenantCreate(TenantBase):
    """
    创建租户的请求模型 (使用 Annotated 类型)
    校验逻辑已包含在类型中，无需 @field_validator
    """
    @model_validator(mode='after')
    def check_phones_are_different(self) -> 'TenantCreate':
        """
        校验规则：公司总机电话和联系人电话不能相同。
        """
        if self.company_phone and self.contact_phone and self.company_phone == self.contact_phone:
            raise ValueError('主要联系人电话不能与公司总机电话相同。')
        return self


class TenantUpdate(BaseModel):
    """
    更新租户的请求模型 (使用 Annotated 类型)
    所有字段都是可选的，只更新提供的字段
    """
    company_name: Optional[NotEmptyStr] = Field(None, min_length=1, max_length=100, description="租户名称")
    company_address: Optional[NotEmptyStr] = Field(None, min_length=1, max_length=255, description="公司地址")
    company_phone: Optional[PhoneStr] = Field(None, min_length=1, max_length=20, description="公司电话")
    company_email: Optional[EmailStr] = Field(None, min_length=1, max_length=100, description="公司邮箱")
    company_website: Optional[str] = Field(None, max_length=255, description="公司网站")
    company_logo: Optional[str] = Field(None, max_length=255, description="公司Logo")
    contact_person: Optional[NotEmptyStr] = Field(None, min_length=1, max_length=20, description="联系人姓名")
    contact_phone: Optional[PhoneStr] = Field(None, min_length=1, max_length=20, description="联系人电话")
    subdomain: Optional[SubdomainStr] = Field(None, min_length=3, max_length=100, description="子域名")

    @model_validator(mode='after')
    def check_phones_are_different_on_update(self) -> 'TenantUpdate':
        """
        更新时校验：如果同时提供了公司电话和联系人电话，则不能相同。
        """
        if self.company_phone and self.contact_phone and self.company_phone == self.contact_phone:
            raise ValueError('主要联系人电话不能与公司总机电话相同。')
        return self


class TenantResponse(TenantBase):
    """
    租户响应模型
    
    用于所有返回单个租户信息的端点
    """
    id: int = Field(..., description="租户唯一标识符")
    is_active: bool = Field(..., description="租户激活状态")
    is_deleted: bool = Field(..., description="软删除标记")
    deleted_at: Optional[datetime] = Field(None, description="删除时间")
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
    company_name: str
    is_active: bool = True
    message: str = "租户已激活"


class TenantDeactivate(BaseModel):
    """租户停用操作响应"""
    id: int
    company_name: str
    is_active: bool = False
    message: str = "租户已停用"


class TenantStats(BaseModel):
    """租户统计信息响应"""
    id: int
    company_name: str
    subdomain: str
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
                    {
                        "company_name": "ABC教育公司",
                        "company_address": "北京市朝阳区xxx街道",
                        "company_phone": "010-12345678",
                        "company_email": "contact@abc.com",
                        "contact_person": "张三",
                        "contact_phone": "13800138000",
                        "subdomain": "abc-edu"
                    },
                    {
                        "company_name": "XYZ科技公司",
                        "company_address": "上海市浦东新区xxx路",
                        "company_phone": "021-87654321",
                        "company_email": "info@xyz.com",
                        "contact_person": "李四",
                        "contact_phone": "13900139000",
                        "subdomain": "xyz-tech"
                    }
                ]
            }
        }
    }


class TenantBulkResponse(BaseModel):
    """批量操作响应模型"""
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    results: list[dict] = Field(..., description="操作结果详情")