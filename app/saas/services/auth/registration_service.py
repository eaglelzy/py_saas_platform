"""顾问注册服务，封装账号与租户初始化逻辑。"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Tuple
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.saas.core.security.password import get_password_hash
from app.saas.models.tenant import PlanCode, Tenant, TenantStatus
from app.saas.models.tenant_member import TenantMember, TenantMemberRole, TenantMemberStatus
from app.saas.models.tenant_subscription import SubscriptionStatus, TenantSubscription
from app.saas.models.user import User
from app.saas.schemas.auth import ConsultantRegisterRequest
from app.saas.services.exceptions import ConflictError
from app.saas.services.tenants.repository import TenantRepository


class ConsultantRegistrationService:
    """负责顾问账号注册、租户初始化与默认订阅配置。"""

    def __init__(self) -> None:
        self.tenant_repo = TenantRepository()

    def register(
        self,
        db: Session,
        payload: ConsultantRegisterRequest,
        *,
        trial_days: int = 14,
    ) -> tuple[User, Tenant, TenantSubscription]:
        """创建用户、租户与订阅，返回关键实体。"""

        existing_user = db.execute(select(User).where(User.email == payload.email)).scalars().first()
        if existing_user:
            raise ConflictError("邮箱已注册，请直接登录", code="user_exists")

        if payload.phone_number:
            existing_phone = (
                db.execute(select(User).where(User.phone_number == payload.phone_number)).scalars().first()
            )
            if existing_phone:
                raise ConflictError("手机号已绑定其他账号", code="phone_exists")

        now = datetime.now(timezone.utc)
        user = User(
            email=payload.email,
            hashed_password=get_password_hash(payload.password),
            display_name=payload.display_name or payload.full_name or payload.email.split("@")[0],
            full_name=payload.full_name or payload.display_name,
            phone_number=payload.phone_number,
            is_active=True,
            is_locked=False,
            # timezone=payload.timezone or "Asia/Shanghai",
        )
        db.add(user)
        db.flush()

        tenant_name = self._generate_tenant_name(db, payload.workspace_name, user.display_name)
        slug = self._generate_slug(db, slug=None, tenant_name=tenant_name, email=user.email)

        tenant = Tenant(
            name=tenant_name,
            slug=slug,
            primary_owner_id=user.id,
            status=TenantStatus.ACTIVE,
            plan_code=PlanCode.FREE,
            member_limit=1,
            contact_name=payload.full_name or user.display_name or tenant_name,
            contact_email=payload.email,
            contact_phone=payload.phone_number or "N/A",
            # timezone=payload.timezone or "Asia/Shanghai",
            activated_at=now,
            trial_ends_at=now + timedelta(days=trial_days),
            notes=self._build_notes(payload),
        )
        db.add(tenant)
        db.flush()

        member = TenantMember(
            tenant_id=tenant.id,
            user_id=user.id,
            role=TenantMemberRole.OWNER,
            status=TenantMemberStatus.ACTIVE,
            activated_at=now,
        )
        db.add(member)

        subscription = TenantSubscription(
            tenant_id=tenant.id,
            plan_id=None,
            plan_code=PlanCode.FREE.value,
            status=SubscriptionStatus.TRIALING,
            starts_at=now,
            trial_ends_at=now + timedelta(days=trial_days),
            member_limit=1,
            price_cents=0,
            currency="CNY",
            auto_renew=False,
            cancel_at_period_end=False,
        )
        db.add(subscription)

        db.commit()
        db.refresh(user)
        db.refresh(tenant)
        db.refresh(subscription)
        return user, tenant, subscription

    def _generate_tenant_name(
        self,
        db: Session,
        workspace_name: str | None,
        display_name: str,
    ) -> str:
        base_name = (workspace_name or f"{display_name}的工作台").strip()
        candidate = base_name
        suffix = 1
        while self.tenant_repo.get_by_name(db, name=candidate):
            suffix += 1
            candidate = f"{base_name} ({suffix})"
        return candidate

    def _generate_slug(
        self,
        db: Session,
        provided_slug: str | None,
        tenant_name: str,
        email: str,
    ) -> str:
        if provided_slug:
            slug = provided_slug
        else:
            base_source = tenant_name or email.split("@")[0]
            normalized = re.sub(r"[^a-z0-9]+", "-", base_source.lower()).strip("-")
            slug = normalized or f"tenant-{uuid4().hex[:6]}"
        candidate = slug
        idx = 1
        while self.tenant_repo.get_by_slug(db, slug=candidate):
            idx += 1
            candidate = f"{slug}-{idx}"
        return candidate

    def _build_notes(self, payload: ConsultantRegisterRequest) -> str | None:
        extras: list[str] = []
        if payload.service_country:
            extras.append(f"服务国家: {payload.service_country}")
        if payload.experience_years is not None:
            extras.append(f"从业年限: {payload.experience_years}")
        return "\n".join(extras) if extras else None


__all__ = ("ConsultantRegistrationService",)
