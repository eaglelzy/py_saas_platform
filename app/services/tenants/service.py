"""租户相关领域服务。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
import secrets

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.core.config.settings import settings
from app.models.tenant import Tenant, TenantStatus, PlanCode
from app.models.tenant_application import ApplicationStatus, TenantApplication
from app.models.user import User
from app.models.tenant_member import TenantMember, TenantMemberRole, TenantMemberStatus
from app.schemas.tenants import TenantCreate, TenantPlanUpdate, TenantUpdate
from app.schemas.applications import TenantApplicationReview, TenantApplicationSubmit
from app.schemas.common import PaginatedResponse
from app.services.exceptions import ConflictError, ValidationError
from app.services.pagination import PaginationParams, build_paginated_response, paginate_stmt
from app.services.tenants.repository import TenantApplicationRepository, TenantRepository
from app.services.notifications import NotificationService
from app.services.auth.activation_service import ActivationTokenService
from app.core.security.password import get_password_hash


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
        self.tenant_repo = TenantRepository()

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
        activation_service: Optional[ActivationTokenService] = None,
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
        activation_token_value: Optional[str] = None
        activation_link: Optional[str] = None
        if payload.status == ApplicationStatus.APPROVED:
            if tenant_service is None:
                raise ValidationError("审批通过需要提供 tenant_service", code="tenant_service_required")

            owner = self._ensure_owner_user(db, application)

            if payload.tenant_id:
                application.tenant_id = payload.tenant_id
            else:
                slug = application.company_name.lower().replace(" ", "-")
                tenant_payload = TenantCreate(
                    name=application.company_name,
                    slug=slug,
                    primary_owner_id=str(owner.id),
                    plan_code=PlanCode.FREE,
                    member_limit=5,
                    contact_name=application.contact_name,
                    contact_email=application.contact_email,
                    contact_phone=application.contact_phone,
                    timezone="Asia/Shanghai",
                )
                created_tenant = tenant_service.create_tenant(db, tenant_payload)
                application.tenant_id = str(created_tenant.id)

            if activation_service is None:
                raise ValidationError("审批通过需要 activation_service", code="activation_service_required")
            activation_record = activation_service.create_or_refresh(db, user=owner)
            activation_token_value = activation_record.token
            activation_link = f"{settings.frontend_activation_url}?token={activation_token_value}"
            if application.tenant_id:
                self._ensure_owner_membership(db, UUID(application.tenant_id), owner)

        db.add(application)
        db.commit()
        db.refresh(application)

        notifier = notification_service or NotificationService()
        if payload.status == ApplicationStatus.APPROVED:
            notifier.send_application_approved(
                application,
                token=activation_token_value or "",
                tenant=created_tenant,
                activation_url=activation_link,
            )
        else:
            notifier.send_application_rejected(application)
        return application

    def _ensure_owner_user(self, db: Session, application: TenantApplication) -> User:
        owner: Optional[User] = None
        if application.submitted_by_user_id:
            owner = db.get(User, application.submitted_by_user_id)
        if owner:
            return owner

        stmt = select(User).where(User.email == application.contact_email)
        owner = db.execute(stmt).scalars().first()
        if owner:
            application.submitted_by_user_id = owner.id
            db.add(application)
            return owner

        owner = User(
            email=application.contact_email,
            hashed_password=get_password_hash(secrets.token_urlsafe(16)),
            full_name=application.contact_name,
            display_name=application.contact_name,
            is_active=False,
            is_locked=False,
            is_superuser=True
        )
        db.add(owner)
        db.flush()
        application.submitted_by_user_id = owner.id
        db.add(application)
        return owner

    def _ensure_owner_membership(self, db: Session, tenant_id: UUID, owner: User) -> None:
        stmt = select(TenantMember).where(
            TenantMember.tenant_id == tenant_id,
            TenantMember.user_id == owner.id,
        )
        member = db.execute(stmt).scalars().first()
        now = datetime.now(timezone.utc)
        if member:
            member.role = TenantMemberRole.OWNER
            member.status = TenantMemberStatus.ACTIVE
            member.activated_at = now
            db.add(member)
            return

        member = TenantMember(
            tenant_id=tenant_id,
            user_id=owner.id,
            role=TenantMemberRole.OWNER,
            status=TenantMemberStatus.ACTIVE,
            activated_at=now,
            invited_by_id=owner.id,
        )
        db.add(member)
