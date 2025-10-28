"""租户入驻申请相关 schema。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import EmailStr, Field, field_validator

from app.saas.models.tenant_application import ApplicationStatus, ReviewStatus
from app.saas.schemas.common import IDMixin, ORMBaseModel, TimestampMixin
from app.saas.utils import validate_phone


class AttachmentSchema(ORMBaseModel):
    """申请附件信息。"""

    name: str = Field(description="附件名称")
    url: str = Field(description="附件访问地址")
    metadata: Optional[dict[str, Any]] = Field(default=None, description="附加信息")


class TenantApplicationSubmit(ORMBaseModel):
    """提交入驻申请请求体。"""

    company_name: str = Field(min_length=2, max_length=200, description="公司名称")
    contact_name: str = Field(min_length=1, max_length=120, description="联系人姓名")
    contact_email: EmailStr = Field(description="联系人邮箱")
    contact_phone: str = Field(min_length=5, max_length=32, description="联系人电话")
    business_description: Optional[str] = Field(default=None, description="业务简介")
    attachments: Optional[list[AttachmentSchema]] = Field(
        default=None,
        description="附件列表，可包含营业执照等证明",
    )
    submitted_by_user_id: Optional[str] = Field(default=None, description="提交人用户 ID")

    @field_validator("contact_phone")
    @classmethod
    def validate_contact_phone(cls, value: str) -> str:
        return validate_phone(value)


class TenantApplicationReview(ORMBaseModel):
    """运营审核申请请求体。"""

    status: ReviewStatus = Field(description="目标审核状态，需为 APPROVED 或 REJECTED")
    reviewer_id: str = Field(description="审核人用户 ID")
    rejection_reason: Optional[str] = Field(default=None, description="拒绝原因，当状态为 REJECTED 时必填")
    notes: Optional[str] = Field(default=None, description="运营备注")
    tenant_id: Optional[str] = Field(
        default=None,
        description="审核通过后关联的租户 ID，可在通过时填写",
    )


class TenantApplicationRead(IDMixin, ORMBaseModel, TimestampMixin):
    """入驻申请读取结构。"""

    company_name: str = Field(description="公司名称")
    contact_name: str = Field(description="联系人姓名")
    contact_email: EmailStr = Field(description="联系人邮箱")
    contact_phone: str = Field(description="联系人电话")
    business_description: Optional[str] = Field(default=None, description="业务简介")
    attachments: Optional[list[AttachmentSchema]] = Field(default=None, description="附件列表")
    submitted_by_user_id: Optional[str] = Field(default=None, description="提交人用户 ID")
    tenant_id: Optional[str] = Field(default=None, description="关联租户 ID")
    status: ApplicationStatus = Field(description="审核状态")
    reviewed_by_user_id: Optional[str] = Field(default=None, description="审核人 ID")
    reviewed_at: Optional[datetime] = Field(default=None, description="审核时间")
    rejection_reason: Optional[str] = Field(default=None, description="拒绝原因")
    notes: Optional[str] = Field(default=None, description="运营备注")


class TenantApplicationSummary(IDMixin, ORMBaseModel):
    """申请列表展示结构。"""

    company_name: str = Field(description="公司名称")
    status: ApplicationStatus = Field(description="审核状态")
    submitted_by_user_id: Optional[str] = Field(default=None, description="提交人")
    reviewed_by_user_id: Optional[str] = Field(default=None, description="审核人")
