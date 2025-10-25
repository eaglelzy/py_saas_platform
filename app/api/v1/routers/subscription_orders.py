"""订阅订单路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import (
    get_db_session,
    subscription_order_service,
    tenant_subscription_service,
)
from app.schemas.common import PaginatedResponse
from app.schemas.orders import SubscriptionOrderCreate, SubscriptionOrderRead, SubscriptionOrderProcess
from app.services.exceptions import NotFoundError, ValidationError
from app.services.pagination import PaginationParams
from app.services.subscriptions.service import SubscriptionOrderService, TenantSubscriptionService
from app.models.subscription_order import SubscriptionOrderStatus

router = APIRouter(prefix="/subscription-orders", tags=["subscription-orders"])


@router.post("", response_model=SubscriptionOrderRead, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: SubscriptionOrderCreate,
    db: Session = Depends(get_db_session),
    service: SubscriptionOrderService = Depends(subscription_order_service),
) -> SubscriptionOrderRead:
    try:
        order = service.create_order(db, payload)
        return SubscriptionOrderRead.model_validate(order)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", response_model=PaginatedResponse[SubscriptionOrderRead])
def list_orders(
    page: int = 1,
    size: int = 20,
    tenant_id: str | None = None,
    status_filter: str | None = None,
    db: Session = Depends(get_db_session),
    service: SubscriptionOrderService = Depends(subscription_order_service),
) -> PaginatedResponse[SubscriptionOrderRead]:
    params = PaginationParams(page=page, size=size)
    status_enum: SubscriptionOrderStatus | None = None
    if status_filter:
        try:
            status_enum = SubscriptionOrderStatus[status_filter.upper()]
        except KeyError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid status filter")
    result = service.list_orders(db, params, tenant_id=tenant_id, status=status_enum)
    return PaginatedResponse[SubscriptionOrderRead](
        items=[SubscriptionOrderRead.model_validate(item) for item in result.items],
        meta=result.meta,
    )


@router.get("/{order_id}", response_model=SubscriptionOrderRead)
def get_order(
    order_id: str,
    db: Session = Depends(get_db_session),
    service: SubscriptionOrderService = Depends(subscription_order_service),
) -> SubscriptionOrderRead:
    try:
        order = service.get_order(db, order_id)
        return SubscriptionOrderRead.model_validate(order)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{order_id}/process", response_model=SubscriptionOrderRead)
def process_order(
    order_id: str,
    payload: SubscriptionOrderProcess,
    db: Session = Depends(get_db_session),
    service: SubscriptionOrderService = Depends(subscription_order_service),
    subscription_service: TenantSubscriptionService = Depends(tenant_subscription_service),
) -> SubscriptionOrderRead:
    try:
        order = service.process_order(db, order_id, payload, subscription_service=subscription_service)
        return SubscriptionOrderRead.model_validate(order)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
