"""订阅相关仓储。"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.saas.models.subscription_order import SubscriptionOrder, SubscriptionOrderStatus
from app.saas.models.subscription_plan import SubscriptionPlan
from app.saas.models.tenant_subscription import SubscriptionStatus, TenantSubscription
from app.saas.services.base import CRUDRepository


class SubscriptionPlanRepository(CRUDRepository[SubscriptionPlan]):
    """套餐配置仓储。"""

    def __init__(self) -> None:
        super().__init__(SubscriptionPlan)

    def get_by_code(self, db: Session, *, code: str) -> Optional[SubscriptionPlan]:
        stmt = select(SubscriptionPlan).where(SubscriptionPlan.code == code)
        return db.execute(stmt).scalars().first()

    def list_active(self, db: Session) -> list[SubscriptionPlan]:
        stmt = select(SubscriptionPlan).where(SubscriptionPlan.is_active.is_(True))
        return db.execute(stmt).scalars().all()


class TenantSubscriptionRepository(CRUDRepository[TenantSubscription]):
    """租户订阅仓储。"""

    def __init__(self) -> None:
        super().__init__(TenantSubscription)

    def get_current(self, db: Session, *, tenant_id: str) -> Optional[TenantSubscription]:
        stmt = (
            select(TenantSubscription)
            .where(
                TenantSubscription.tenant_id == tenant_id,
                TenantSubscription.status.in_([SubscriptionStatus.TRIALING, SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE]),
            )
            .order_by(TenantSubscription.starts_at.desc())
        )
        return db.execute(stmt).scalars().first()

    def list_by_tenant(self, db: Session, *, tenant_id: str) -> list[TenantSubscription]:
        stmt: Select[tuple[TenantSubscription]] = (
            select(TenantSubscription)
            .where(TenantSubscription.tenant_id == tenant_id)
            .order_by(TenantSubscription.created_at.desc())
        )
        return db.execute(stmt).scalars().all()


class SubscriptionOrderRepository(CRUDRepository[SubscriptionOrder]):
    """订阅订单仓储。"""

    def __init__(self) -> None:
        super().__init__(SubscriptionOrder)

    def list_pending(self, db: Session, *, tenant_id: Optional[str] = None) -> list[SubscriptionOrder]:
        stmt = select(SubscriptionOrder).where(SubscriptionOrder.status == SubscriptionOrderStatus.PENDING)
        if tenant_id:
            stmt = stmt.where(SubscriptionOrder.tenant_id == tenant_id)
        return db.execute(stmt).scalars().all()

    def get_pending(self, db: Session, *, order_id: str) -> Optional[SubscriptionOrder]:
        stmt = select(SubscriptionOrder).where(
            SubscriptionOrder.id == order_id,
            SubscriptionOrder.status == SubscriptionOrderStatus.PENDING,
        )
        return db.execute(stmt).scalars().first()

    def count_pending_by_tenant(self, db: Session, *, tenant_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(SubscriptionOrder)
            .where(
                SubscriptionOrder.tenant_id == tenant_id,
                SubscriptionOrder.status == SubscriptionOrderStatus.PENDING,
            )
        )
        return db.execute(stmt).scalar_one()
