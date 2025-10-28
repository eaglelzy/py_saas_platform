"""API 层依赖定义。"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.saas.api.v1.auth_utils import require_permissions, resolve_current_tenant, resolve_current_user
from app.saas.core.tenancy import TenantContext
from app.saas.db.session import get_db
from app.saas.models.user import User
from app.saas.services.auth.activation_service import ActivationTokenService
from app.saas.services.auth.registration_service import ConsultantRegistrationService
from app.saas.services.auth.refresh_service import RefreshTokenService
from app.saas.services.audit import AuditService
from app.saas.services.auth.token_blacklist_service import TokenBlacklistService
from app.saas.services.members.service import MemberInvitationService, TenantMemberService
from app.saas.services.notifications import NotificationService
from app.saas.services.security import RateLimiterService
from app.saas.services.subscriptions.service import (
    SubscriptionOrderService,
    SubscriptionPlanService,
    TenantSubscriptionService,
)
from app.saas.services.tenants.service import TenantApplicationService, TenantService
from app.saas.services.verification import VerificationService


def get_db_session(db: Session = Depends(get_db)) -> Session:
    """注入 SQLAlchemy Session。"""

    return db


def tenant_service() -> TenantService:
    return TenantService()


def tenant_application_service() -> TenantApplicationService:
    return TenantApplicationService()


def tenant_member_service() -> TenantMemberService:
    return TenantMemberService()


def member_invitation_service() -> MemberInvitationService:
    return MemberInvitationService()


def subscription_plan_service() -> SubscriptionPlanService:
    return SubscriptionPlanService()


def tenant_subscription_service() -> TenantSubscriptionService:
    return TenantSubscriptionService()


def subscription_order_service() -> SubscriptionOrderService:
    return SubscriptionOrderService()


def notification_service() -> NotificationService:
    return NotificationService()


def activation_token_service() -> ActivationTokenService:
    return ActivationTokenService()


def audit_service() -> AuditService:
    return AuditService()


def refresh_token_service() -> RefreshTokenService:
    return RefreshTokenService()


def consultant_registration_service() -> ConsultantRegistrationService:
    return ConsultantRegistrationService()


def rate_limiter_service() -> RateLimiterService:
    return RateLimiterService()


def token_blacklist_service() -> TokenBlacklistService:
    return TokenBlacklistService()


def verification_code_service() -> VerificationService:
    return VerificationService()


def get_current_user(user: User = Depends(resolve_current_user)) -> User:
    return user


def get_current_tenant(tenant_ctx: TenantContext = Depends(resolve_current_tenant)) -> TenantContext:
    return tenant_ctx


__all__ = (
    "activation_token_service",
    "audit_service",
    "get_current_tenant",
    "get_current_user",
    "get_db_session",
    "member_invitation_service",
    "notification_service",
    "refresh_token_service",
    "consultant_registration_service",
    "require_permissions",
    "subscription_order_service",
    "subscription_plan_service",
    "tenant_application_service",
    "tenant_member_service",
    "tenant_service",
    "tenant_subscription_service",
    "rate_limiter_service",
    "token_blacklist_service",
    "verification_code_service",
)
