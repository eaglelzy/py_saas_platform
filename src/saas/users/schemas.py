"""
用户管理的数据验证模式

定义用户相关的 Pydantic 模型，用于 API 请求和响应的数据验证。
"""

import re
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator, EmailStr


class UserBase(BaseModel):
    """用户基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="用户姓名")
    email: EmailStr = Field(..., description="电子邮箱")
    is_active: bool = Field(True, description="账户是否激活")
    is_superuser: bool = Field(False, description="是否为超级用户")


class UserCreate(UserBase):
    """
    创建用户的请求模型
    
    用于 POST /api/v1/users 端点
    """
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    tenant_id: int = Field(..., description="所属租户ID")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """自定义姓名校验 - 只允许中文、英文、数字和空格"""
        if not v or not v.strip():
            raise ValueError('用户姓名不能为空')

        # 去除首尾空格
        v = v.strip()

        # 检查长度
        if len(v) < 1:
            raise ValueError('用户姓名至少需要1个字符')
        if len(v) > 100:
            raise ValueError('用户姓名不能超过100个字符')

        # 检查是否只包含中文、英文、数字和空格
        if not re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9\s]+$', v):
            raise ValueError('用户姓名只能包含中文字符、英文字母、数字和空格')

        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """密码强度校验"""
        if len(v) < 6:
            raise ValueError('密码至少需要6个字符')
        if len(v) > 100:
            raise ValueError('密码不能超过100个字符')
        
        # 检查密码强度（至少包含字母和数字）
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('密码必须包含至少一个字母')
        if not re.search(r'[0-9]', v):
            raise ValueError('密码必须包含至少一个数字')
            
        return v


class UserUpdate(BaseModel):
    """
    更新用户的请求模型
    
    用于 PUT /api/v1/users/{user_id} 端点
    所有字段都是可选的，只更新提供的字段
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="用户姓名")
    email: Optional[EmailStr] = Field(None, description="电子邮箱")
    is_active: Optional[bool] = Field(None, description="账户是否激活")
    is_superuser: Optional[bool] = Field(None, description="是否为超级用户")
    password: Optional[str] = Field(None, min_length=6, max_length=100, description="新密码")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """自定义姓名校验"""
        if v is None:
            return v

        if not v or not v.strip():
            raise ValueError('用户姓名不能为空')

        v = v.strip()

        if len(v) < 1:
            raise ValueError('用户姓名至少需要1个字符')
        if len(v) > 100:
            raise ValueError('用户姓名不能超过100个字符')

        if not re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9\s]+$', v):
            raise ValueError('用户姓名只能包含中文字符、英文字母、数字和空格')

        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        """密码强度校验"""
        if v is None:
            return v

        if len(v) < 6:
            raise ValueError('密码至少需要6个字符')
        if len(v) > 100:
            raise ValueError('密码不能超过100个字符')
        
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('密码必须包含至少一个字母')
        if not re.search(r'[0-9]', v):
            raise ValueError('密码必须包含至少一个数字')
            
        return v


class UserResponse(UserBase):
    """
    用户响应模型
    
    用于所有返回单个用户信息的端点
    """
    id: int = Field(..., description="用户唯一标识符")
    tenant_id: int = Field(..., description="所属租户ID")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """
    用户列表响应模型
    
    用于 GET /api/v1/users 端点，支持分页
    """
    total: int = Field(..., description="用户总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    items: List[UserResponse] = Field(..., description="用户列表")


class UserPasswordChange(BaseModel):
    """用户密码修改模型"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """新密码强度校验"""
        if len(v) < 6:
            raise ValueError('新密码至少需要6个字符')
        if len(v) > 100:
            raise ValueError('新密码不能超过100个字符')
        
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('新密码必须包含至少一个字母')
        if not re.search(r'[0-9]', v):
            raise ValueError('新密码必须包含至少一个数字')
            
        return v


class UserActivate(BaseModel):
    """用户激活操作响应"""
    id: int
    name: str
    is_active: bool = True
    message: str = "用户已激活"


class UserDeactivate(BaseModel):
    """用户停用操作响应"""
    id: int
    name: str
    is_active: bool = False
    message: str = "用户已停用"


class UserStats(BaseModel):
    """用户统计信息响应模型"""
    id: int = Field(..., description="用户唯一标识符")
    name: str = Field(..., description="用户姓名")
    email: str = Field(..., description="电子邮箱")
    tenant_name: str = Field(..., description="所属租户名称")
    total_students: int = Field(..., description="负责的学生总数")
    last_activity: Optional[datetime] = Field(None, description="最近活动时间")


class UserSearchParams(BaseModel):
    """用户搜索参数模型"""
    name: Optional[str] = Field(None, description="按姓名搜索")
    email: Optional[str] = Field(None, description="按邮箱搜索")
    is_active: Optional[bool] = Field(None, description="按激活状态筛选")
    is_superuser: Optional[bool] = Field(None, description="按超级用户状态筛选")
    tenant_id: Optional[int] = Field(None, description="按租户筛选")


class UserBulkCreate(BaseModel):
    """批量创建用户模型"""
    users: List[UserCreate] = Field(..., min_length=1, max_length=50, description="用户列表")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "users": [
                    {
                        "name": "张三",
                        "email": "zhangsan@example.com",
                        "password": "password123",
                        "tenant_id": 1
                    },
                    {
                        "name": "李四",
                        "email": "lisi@example.com", 
                        "password": "password456",
                        "tenant_id": 1
                    }
                ]
            }
        }
    }


class UserBulkResponse(BaseModel):
    """批量操作响应模型"""
    success_count: int = Field(..., description="成功创建的用户数量")
    failed_count: int = Field(..., description="创建失败的用户数量")
    errors: List[dict] = Field(..., description="失败详情列表")


class UserLogin(BaseModel):
    """用户登录模型"""
    email: EmailStr = Field(..., description="电子邮箱")
    password: str = Field(..., description="密码")


class UserLoginResponse(BaseModel):
    """用户登录响应模型"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field("bearer", description="令牌类型")
    user: UserResponse = Field(..., description="用户信息")
    expires_in: int = Field(..., description="令牌过期时间（秒）")
