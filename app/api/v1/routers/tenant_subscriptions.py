"""租户订阅路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import (
    get_db_session,
    tenant_subscription_service,
)
from app.schemas.common import PaginatedResponse
from app.schemas.subscriptions import (
    TenantSubscriptionCreate,
    TenantSubscriptionRead,
    TenantSubscriptionUpdate,
)
from app.services.exceptions import NotFoundError, ValidationError
from app.services.pagination import PaginationParams
from app.services.subscriptions.service import TenantSubscriptionService

router = APIRouter(prefix="/tenants/{tenant_id}/subscriptions", tags=["tenant-subscriptions"])


@router.post("", response_model=TenantSubscriptionRead, status_code=status.HTTP_201_CREATED)
def create_subscription(
    tenant_id: str,
    payload: TenantSubscriptionCreate,
    db: Session = Depends(get_db_session),
    service: TenantSubscriptionService = Depends(tenant_subscription_service),
) -> TenantSubscriptionRead:
    payload_data = payload.model_copy(update={"tenant_id": tenant_id})
    try:
        subscription = service.create_subscription(db, payload_data)
        return TenantSubscriptionRead.model_validate(subscription)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", response_model=PaginatedResponse[TenantSubscriptionRead])
def list_subscriptions(
    tenant_id: str,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db_session),
    service: TenantSubscriptionService = Depends(tenant_subscription_service),
) -> PaginatedResponse[TenantSubscriptionRead]:
    params = PaginationParams(page=page, size=size)
    result = service.list_subscriptions(db, tenant_id, params)
    return PaginatedResponse[TenantSubscriptionRead](
        items=[TenantSubscriptionRead.model_validate(item) for item in result.items],
        meta=result.meta,
    )


@router.get("/{subscription_id}", response_model=TenantSubscriptionRead)
def get_subscription(
    tenant_id: str,
    subscription_id: str,
    db: Session = Depends(get_db_session),
    service: TenantSubscriptionService = Depends(tenant_subscription_service),
) -> TenantSubscriptionRead:
    try:
        subscription = service.get_subscription(db, subscription_id)
        if str(subscription.tenant_id) != tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="subscription not found")
        return TenantSubscriptionRead.model_validate(subscription)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{subscription_id}", response_model=TenantSubscriptionRead)
def update_subscription(
    tenant_id: str,
    subscription_id: str,
    payload: TenantSubscriptionUpdate,
    db: Session = Depends(get_db_session),
    service: TenantSubscriptionService = Depends(tenant_subscription_service),
) -> TenantSubscriptionRead:
    try:
        subscription = service.update_subscription(db, subscription_id, payload)
        if str(subscription.tenant_id) != tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="subscription not found")
        return TenantSubscriptionRead.model_validate(subscription)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
