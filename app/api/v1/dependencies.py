"""API 层依赖定义。"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.tenants.service import TenantService, TenantApplicationService
from app.services.members.service import TenantMemberService, MemberInvitationService
from app.services.subscriptions.service import (
    SubscriptionOrderService,
    SubscriptionPlanService,
    TenantSubscriptionService,
)
from app.services.notifications import NotificationService


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
