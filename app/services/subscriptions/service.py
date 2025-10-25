"""订阅套餐、租户订阅与订单的业务逻辑。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.subscription_order import SubscriptionOrder, SubscriptionOrderStatus
from app.models.subscription_plan import SubscriptionPlan
from app.models.tenant import PlanCode
from app.models.tenant_subscription import SubscriptionStatus, TenantSubscription
from app.schemas.common import PaginatedResponse
from app.schemas.orders import SubscriptionOrderCreate, SubscriptionOrderProcess
from app.schemas.subscriptions import (
    SubscriptionPlanCreate,
    SubscriptionPlanRead,
    SubscriptionPlanUpdate,
    TenantSubscriptionCreate,
    TenantSubscriptionRead,
    TenantSubscriptionUpdate,
)
from app.services.exceptions import ConflictError, NotFoundError, ValidationError
from app.services.pagination import PaginationParams, build_paginated_response, paginate_stmt
from app.services.subscriptions.repository import (
    SubscriptionOrderRepository,
    SubscriptionPlanRepository,
    TenantSubscriptionRepository,
)
from app.services.tenants.repository import TenantRepository


class SubscriptionPlanService:
    """订阅套餐管理。"""

    def __init__(self) -> None:
        self.repo = SubscriptionPlanRepository()

    def create_plan(self, db: Session, payload: SubscriptionPlanCreate) -> SubscriptionPlan:
        if self.repo.get_by_code(db, code=payload.code):
            raise ConflictError("套餐代码已存在", code="subscription_plan_exists")
        plan = self.repo.create(db, obj_in=payload)
        db.commit()
        db.refresh(plan)
        return plan

    def list_plans(
        self,
        db: Session,
        params: PaginationParams,
        *,
        only_active: bool = False,
    ) -> PaginatedResponse[SubscriptionPlan]:
        stmt: Select[tuple[SubscriptionPlan]] = select(SubscriptionPlan)
        if only_active:
            stmt = stmt.where(SubscriptionPlan.is_active.is_(True))
        stmt = stmt.order_by(SubscriptionPlan.created_at.desc())
        items, meta = paginate_stmt(db, stmt, params)
        return build_paginated_response(items, meta)

    def get_plan(self, db: Session, plan_id: str) -> SubscriptionPlan:
        plan = self.repo.get(db, id=plan_id)
        if not plan:
            raise NotFoundError("套餐不存在", code="subscription_plan_not_found")
        return plan

    def get_by_code(self, db: Session, code: str) -> SubscriptionPlan:
        plan = self.repo.get_by_code(db, code=code)
        if not plan:
            raise NotFoundError("套餐不存在", code="subscription_plan_not_found")
        return plan

    def update_plan(self, db: Session, plan_id: str, payload: SubscriptionPlanUpdate) -> SubscriptionPlan:
        plan = self.get_plan(db, plan_id)
        updated = self.repo.update(db, db_obj=plan, obj_in=payload)
        db.commit()
        db.refresh(updated)
        return updated

    def toggle_plan(self, db: Session, plan_id: str, *, is_active: bool) -> SubscriptionPlan:
        plan = self.get_plan(db, plan_id)
        plan.is_active = is_active
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan


class TenantSubscriptionService:
    """租户订阅管理。"""

    def __init__(self) -> None:
        self.subscription_repo = TenantSubscriptionRepository()
        self.plan_repo = SubscriptionPlanRepository()
        self.tenant_repo = TenantRepository()

    def _resolve_plan(self, db: Session, payload: TenantSubscriptionCreate) -> SubscriptionPlan:
        if payload.plan_id:
            plan = self.plan_repo.get(db, id=payload.plan_id)
            if not plan:
                raise ValidationError("指定的 plan_id 无效", code="plan_not_found")
            if plan.code != payload.plan_code:
                raise ValidationError("plan_id 与 plan_code 不一致", code="plan_code_mismatch")
            return plan
        plan = self.plan_repo.get_by_code(db, code=payload.plan_code)
        if not plan:
            raise ValidationError("套餐不存在", code="plan_not_found")
        return plan

    def create_subscription(
        self,
        db: Session,
        payload: TenantSubscriptionCreate,
    ) -> TenantSubscription:
        tenant = self.tenant_repo.get_or_raise(db, id=payload.tenant_id)
        plan = self._resolve_plan(db, payload)

        current = self.subscription_repo.get_current(db, tenant_id=payload.tenant_id)
        if current and current.status in {SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING}:
            current.status = SubscriptionStatus.EXPIRED
            current.ends_at = payload.starts_at or datetime.now(timezone.utc)
            db.add(current)

        data = payload.model_dump(exclude_unset=True)
        data.setdefault("member_limit", plan.member_limit)
        data.setdefault("price_cents", plan.price_cents)
        data.setdefault("currency", plan.currency)
        subscription = self.subscription_repo.create(db, obj_in=data)

        normalized_code = plan.code.upper()
        if normalized_code in PlanCode.__members__:
            tenant.plan_code = PlanCode[normalized_code]
        tenant.member_limit = data["member_limit"]
        if payload.starts_at:
            tenant.activated_at = payload.starts_at
        if payload.trial_ends_at:
            tenant.trial_ends_at = payload.trial_ends_at
        elif payload.ends_at and tenant.trial_ends_at is None:
            tenant.trial_ends_at = payload.ends_at
        db.add(tenant)

        db.commit()
        db.refresh(subscription)
        return subscription

    def list_subscriptions(
        self,
        db: Session,
        tenant_id: str,
        params: PaginationParams,
    ) -> PaginatedResponse[TenantSubscription]:
        stmt: Select[tuple[TenantSubscription]] = (
            select(TenantSubscription)
            .where(TenantSubscription.tenant_id == tenant_id)
            .order_by(TenantSubscription.created_at.desc())
        )
        items, meta = paginate_stmt(db, stmt, params)
        return build_paginated_response(items, meta)

    def get_subscription(self, db: Session, subscription_id: str) -> TenantSubscription:
        subscription = self.subscription_repo.get(db, id=subscription_id)
        if not subscription:
            raise NotFoundError("订阅不存在", code="tenant_subscription_not_found")
        return subscription

    def update_subscription(
        self,
        db: Session,
        subscription_id: str,
        payload: TenantSubscriptionUpdate,
    ) -> TenantSubscription:
        subscription = self.get_subscription(db, subscription_id)
        updated = self.subscription_repo.update(db, db_obj=subscription, obj_in=payload)
        db.commit()
        db.refresh(updated)
        return updated

    def set_status(
        self,
        db: Session,
        subscription_id: str,
        *,
        status: SubscriptionStatus,
    ) -> TenantSubscription:
        subscription = self.get_subscription(db, subscription_id)
        subscription.status = status
        if status in {SubscriptionStatus.CANCELLED, SubscriptionStatus.EXPIRED}:
            subscription.ends_at = subscription.ends_at or datetime.now(timezone.utc)
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        return subscription

    def get_current(self, db: Session, tenant_id: str) -> Optional[TenantSubscription]:
        return self.subscription_repo.get_current(db, tenant_id=tenant_id)


class SubscriptionOrderService:
    """订阅订单管理。"""

    def __init__(self) -> None:
        self.order_repo = SubscriptionOrderRepository()
        self.tenant_repo = TenantRepository()
        self.plan_repo = SubscriptionPlanRepository()
        self.subscription_repo = TenantSubscriptionRepository()

    def create_order(self, db: Session, payload: SubscriptionOrderCreate) -> SubscriptionOrder:
        tenant = self.tenant_repo.get_or_raise(db, id=payload.tenant_id)
        if self.order_repo.count_pending_by_tenant(db, tenant_id=payload.tenant_id) >= 5:
            raise ValidationError("该租户待处理订单过多", code="pending_orders_limit")
        self.plan_repo.get_by_code(db, code=payload.target_plan_code)  # 确认目标套餐存在
        order = self.order_repo.create(db, obj_in=payload)
        db.commit()
        db.refresh(order)
        return order

    def list_orders(
        self,
        db: Session,
        params: PaginationParams,
        *,
        tenant_id: Optional[str] = None,
        status: Optional[SubscriptionOrderStatus] = None,
    ) -> PaginatedResponse[SubscriptionOrder]:
        stmt: Select[tuple[SubscriptionOrder]] = select(SubscriptionOrder)
        if tenant_id:
            stmt = stmt.where(SubscriptionOrder.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(SubscriptionOrder.status == status)
        stmt = stmt.order_by(SubscriptionOrder.created_at.desc())
        items, meta = paginate_stmt(db, stmt, params)
        return build_paginated_response(items, meta)

    def get_order(self, db: Session, order_id: str) -> SubscriptionOrder:
        order = self.order_repo.get(db, id=order_id)
        if not order:
            raise NotFoundError("订单不存在", code="subscription_order_not_found")
        return order

    def process_order(
        self,
        db: Session,
        order_id: str,
        payload: SubscriptionOrderProcess,
        *,
        subscription_service: Optional[TenantSubscriptionService] = None,
    ) -> SubscriptionOrder:
        order = self.order_repo.get_pending(db, order_id=order_id)
        if not order:
            raise ValidationError("仅待处理订单可操作", code="order_not_pending")

        order.status = payload.status
        order.processed_by_user_id = payload.processed_by_user_id
        order.payment_reference = payload.payment_reference
        order.processed_at = payload.processed_at or datetime.now(timezone.utc)
        order.paid_at = payload.paid_at
        order.expires_at = payload.expires_at
        order.notes = payload.notes

        if order.status == SubscriptionOrderStatus.PAID:
            db.add(order)
            db.commit()
            db.refresh(order)
            return order

        if order.status == SubscriptionOrderStatus.APPROVED and subscription_service:
            plan = self.plan_repo.get_by_code(db, code=order.target_plan_code)
            if not plan:
                raise ValidationError("目标套餐不存在", code="plan_not_found")
            subscription_payload = TenantSubscriptionCreate(
                tenant_id=str(order.tenant_id),
                plan_id=str(order.target_plan_id) if order.target_plan_id else None,
                plan_code=order.target_plan_code,
                status=SubscriptionStatus.ACTIVE,
                starts_at=datetime.now(timezone.utc),
                member_limit=plan.member_limit,
                price_cents=order.amount_cents,
                currency=order.currency,
            )
            subscription_service.create_subscription(db, subscription_payload)
            order.status = SubscriptionOrderStatus.PAID
            order.paid_at = order.paid_at or datetime.now(timezone.utc)

        db.add(order)
        db.commit()
        db.refresh(order)
        return order
