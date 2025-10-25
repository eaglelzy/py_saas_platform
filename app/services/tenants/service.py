"""租户相关领域服务。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.tenant import Tenant, TenantStatus, PlanCode
from app.models.tenant_application import ApplicationStatus, TenantApplication
from app.schemas.tenants import TenantCreate, TenantPlanUpdate, TenantUpdate
from app.schemas.applications import TenantApplicationReview, TenantApplicationSubmit
from app.schemas.common import PaginatedResponse
from app.services.exceptions import ConflictError, ValidationError
from app.services.pagination import PaginationParams, build_paginated_response, paginate_stmt
from app.services.tenants.repository import TenantApplicationRepository, TenantRepository
from app.services.notifications import NotificationService


class TenantService:
    """租户 CRUD 及业务逻辑。"""

    def __init__(self) -> None:
        self.repo = TenantRepository()

    def create_tenant(self, db: Session, payload: TenantCreate) -> Tenant:
        if self.repo.get_by_slug(db, slug=payload.slug):
            raise ConflictError("租户标识已存在", code="tenant_slug_exists")
        if self.repo.get_by_name(db, name=payload.name):
            raise ConflictError("租户名称已存在", code="tenant_name_exists")
        payload_data = payload.model_dump()
        payload_data["primary_owner_id"] = UUID(payload_data["primary_owner_id"])
        tenant = self.repo.create(db, obj_in=payload_data)
        db.commit()
        db.refresh(tenant)
        return tenant

    def get_tenant(self, db: Session, tenant_id: str) -> Tenant:
        return self.repo.get_or_raise(db, id=tenant_id)

    def list_tenants(
        self,
        db: Session,
        params: PaginationParams,
        *,
        status: Optional[TenantStatus] = None,
        search: Optional[str] = None,
    ) -> PaginatedResponse[Tenant]:
        stmt: Select[tuple[Tenant]] = select(Tenant)
        if status:
            stmt = stmt.where(Tenant.status == status)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(Tenant.name.ilike(pattern))
        stmt = stmt.order_by(Tenant.created_at.desc())
        items, meta = paginate_stmt(db, stmt, params)
        return build_paginated_response(items, meta)

    def update_tenant(self, db: Session, tenant_id: str, payload: TenantUpdate) -> Tenant:
        tenant = self.repo.get_or_raise(db, id=tenant_id)
        updated = self.repo.update(db, db_obj=tenant, obj_in=payload)
        db.commit()
        db.refresh(updated)
        return updated

    def update_status(self, db: Session, tenant_id: str, *, status: TenantStatus) -> Tenant:
        tenant = self.repo.get_or_raise(db, id=tenant_id)
        if tenant.status == status:
            return tenant
        tenant.status = status
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        return tenant

    def update_plan(self, db: Session, tenant_id: str, payload: TenantPlanUpdate) -> Tenant:
        tenant = self.repo.get_or_raise(db, id=tenant_id)
        tenant.plan_code = payload.plan_code
        if payload.member_limit is not None:
            tenant.member_limit = payload.member_limit
        if payload.activated_at is not None:
            tenant.activated_at = payload.activated_at
        if payload.expires_at is not None:
            tenant.trial_ends_at = payload.expires_at
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        return tenant

    def delete_tenant(self, db: Session, tenant_id: str) -> None:
        tenant = self.repo.get_or_raise(db, id=tenant_id)
        self.repo.delete(db, db_obj=tenant)
        db.commit()


class TenantApplicationService:
    """租户入驻申请服务。"""

    def __init__(self) -> None:
        self.repo = TenantApplicationRepository()

    def submit(self, db: Session, payload: TenantApplicationSubmit) -> TenantApplication:
        existing = self.repo.find_pending_by_company_and_email(
            db,
            company_name=payload.company_name,
            contact_email=payload.contact_email,
        )
        if existing:
            raise ConflictError("已存在待审核的同公司申请", code="application_pending_exists")

        existing = self.repo.find_pending_by_email(
            db,
            contact_email=payload.contact_email,
        )
        if existing:
            raise ConflictError("已存在待审核的同邮箱申请", code="application_pending_exists")

        application = self.repo.create(db, obj_in=payload)
        db.commit()
        db.refresh(application)
        return application

    def list_applications(
        self,
        db: Session,
        params: PaginationParams,
        *,
        status: Optional[ApplicationStatus] = None,
    ) -> PaginatedResponse[TenantApplication]:
        stmt: Select[tuple[TenantApplication]] = select(TenantApplication)
        if status:
            stmt = stmt.where(TenantApplication.status == status)
        stmt = stmt.order_by(TenantApplication.created_at.desc())
        items, meta = paginate_stmt(db, stmt, params)
        return build_paginated_response(items, meta)

    def get(self, db: Session, application_id: str) -> TenantApplication:
        return self.repo.get_or_raise(db, id=application_id)

    def review(
        self,
        db: Session,
        application_id: str,
        payload: TenantApplicationReview,
        *,
        tenant_service: Optional[TenantService] = None,
        notification_service: Optional[NotificationService] = None,
    ) -> TenantApplication:
        application = self.repo.get_or_raise(db, id=application_id)
        if application.status != ApplicationStatus.PENDING:
            raise ValidationError("申请已审核", code="application_already_reviewed")

        if payload.status not in {ApplicationStatus.APPROVED, ApplicationStatus.REJECTED}:
            raise ValidationError("仅支持将申请标记为通过或拒绝", code="invalid_review_status")

        if payload.status == ApplicationStatus.REJECTED and not payload.rejection_reason:
            raise ValidationError("拒绝申请需要填写原因", code="rejection_reason_required")

        application.status = payload.status
        application.reviewed_by_user_id = payload.reviewer_id
        application.reviewed_at = datetime.now(timezone.utc)
        application.rejection_reason = payload.rejection_reason
        application.notes = payload.notes

        created_tenant: Optional[Tenant] = None
        if payload.status == ApplicationStatus.APPROVED:
            if payload.tenant_id:
                application.tenant_id = payload.tenant_id
            else:
                if tenant_service is None:
                    raise ValidationError("审批通过需要提供 tenant_service", code="tenant_service_required")
                if not application.submitted_by_user_id:
                    raise ValidationError("审批通过需要提交人用户 ID", code="owner_required")
                slug = application.company_name.lower().replace(" ", "-")
                tenant_payload = TenantCreate(
                    name=application.company_name,
                    slug=slug,
                    primary_owner_id=str(application.submitted_by_user_id),
                    plan_code=PlanCode.FREE,
                    member_limit=5,
                    contact_name=application.contact_name,
                    contact_email=application.contact_email,
                    contact_phone=application.contact_phone,
                    timezone="Asia/Shanghai",
                )
                created_tenant = tenant_service.create_tenant(db, tenant_payload)
                application.tenant_id = str(created_tenant.id)

        db.add(application)
        db.commit()
        db.refresh(application)

        notifier = notification_service or NotificationService()
        if payload.status == ApplicationStatus.APPROVED:
            notifier.send_application_approved(application, created_tenant)
        else:
            notifier.send_application_rejected(application)
        return application
