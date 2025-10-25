"""租户成员与邀请相关 schema。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import EmailStr, Field, field_validator

from app.models.member_invitation import InvitationStatus
from app.models.tenant_member import TenantMemberRole, TenantMemberStatus
from app.schemas.common import IDMixin, ORMBaseModel, TimestampMixin
from app.utils import validate_phone, validate_password


class TenantMemberBase(ORMBaseModel):
    """租户成员公共字段。"""

    user_id: str = Field(description="关联的用户 ID")
    role: TenantMemberRole = Field(default=TenantMemberRole.MEMBER, description="租户角色")
    notes: Optional[str] = Field(default=None, description="备注信息")


class TenantMemberCreate(ORMBaseModel):
    """创建租户成员请求体。"""

    user_id: str = Field(description="关联的用户 ID")
    role: TenantMemberRole = Field(default=TenantMemberRole.MEMBER, description="租户角色")
    invited_by_id: Optional[str] = Field(default=None, description="邀请者用户 ID")
    notes: Optional[str] = Field(default=None, description="备注信息")


class TenantMemberUpdate(ORMBaseModel):
    """更新租户成员信息。"""

    role: Optional[TenantMemberRole] = Field(default=None, description="租户角色")
    status: Optional[TenantMemberStatus] = Field(default=None, description="成员状态")
    notes: Optional[str] = Field(default=None, description="备注信息")


class TenantMemberRead(IDMixin, ORMBaseModel, TimestampMixin):
    """租户成员对外输出。"""

    tenant_id: str = Field(description="租户 ID")
    user_id: str = Field(description="用户 ID")
    role: TenantMemberRole = Field(description="租户角色")
    status: TenantMemberStatus = Field(description="成员状态")
    invited_by_id: Optional[str] = Field(default=None, description="邀请者用户 ID")
    activated_at: Optional[datetime] = Field(default=None, description="成员激活时间")
    deactivated_at: Optional[datetime] = Field(default=None, description="成员停用时间")
    last_access_at: Optional[datetime] = Field(default=None, description="最后访问时间")


class TenantMemberSummary(IDMixin, ORMBaseModel):
    """成员列表展示信息。"""

    user_id: str = Field(description="用户 ID")
    role: TenantMemberRole = Field(description="租户角色")
    status: TenantMemberStatus = Field(description="成员状态")


class MemberInvitationCreate(ORMBaseModel):
    """创建成员邀请。"""

    email: EmailStr = Field(description="受邀成员邮箱")
    role: TenantMemberRole = Field(default=TenantMemberRole.MEMBER, description="成员角色")
    message: Optional[str] = Field(default=None, description="邀请附言")

    @field_validator("email")
    @classmethod
    def lower_email(cls, value: EmailStr) -> EmailStr:
        return EmailStr(str(value).lower())


class MemberInvitationRead(IDMixin, ORMBaseModel, TimestampMixin):
    """成员邀请对外输出。"""

    tenant_id: str = Field(description="租户 ID")
    invited_by_id: Optional[str] = Field(default=None, description="邀请者用户 ID")
    user_id: Optional[str] = Field(default=None, description="受邀用户 ID")
    role: TenantMemberRole = Field(description="预设成员角色")
    email: EmailStr = Field(description="受邀成员邮箱")
    token: str = Field(description="邀请 token")
    status: InvitationStatus = Field(description="邀请状态")
    expires_at: Optional[datetime] = Field(default=None, description="邀请过期时间")
    accepted_at: Optional[datetime] = Field(default=None, description="邀请接受时间")
    revoked_at: Optional[datetime] = Field(default=None, description="邀请撤销时间")
    message: Optional[str] = Field(default=None, description="邀请附言")


class InvitationAcceptRequest(ORMBaseModel):
    """受邀用户接受邀请时的请求体。"""

    password: Optional[str] = Field(default=None, min_length=8, description="设置登录密码（当账号未激活时必填）")
    display_name: Optional[str] = Field(default=None, max_length=150, description="用户展示名称")

    @field_validator("password")
    @classmethod
    def validate_password_optional(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return validate_password(value)


class InvitationAcceptResponse(ORMBaseModel):
    """邀请接受后的响应。"""

    member: TenantMemberRead = Field(description="新成员信息")
    tenant_id: str = Field(description="关联租户 ID")
