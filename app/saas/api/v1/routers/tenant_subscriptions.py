"""租户订阅路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.saas.api.v1.api_error import ApiError
from app.saas.api.v1.dependencies import (
    get_db_session,
    tenant_subscription_service,
    require_permissions,
)
from app.saas.core.tenancy import TenantContext
from app.saas.schemas.common import PaginatedResponse
from app.saas.schemas.subscriptions import (
    TenantSubscriptionCreate,
    TenantSubscriptionRead,
    TenantSubscriptionUpdate,
)
from app.saas.services.exceptions import NotFoundError, ValidationError
from app.saas.services.pagination import PaginationParams
from app.saas.services.subscriptions.service import TenantSubscriptionService

router = APIRouter(prefix="/tenants/{tenant_id}/subscriptions", tags=["tenant-subscriptions"])


@router.post("", response_model=TenantSubscriptionRead, status_code=status.HTTP_201_CREATED)
def create_subscription(
    tenant_id: str,
    payload: TenantSubscriptionCreate,
    db: Session = Depends(get_db_session),
    service: TenantSubscriptionService = Depends(tenant_subscription_service),
    tenant_ctx: TenantContext = Depends(require_permissions("tenant:subscription:manage")),
) -> TenantSubscriptionRead:
    if str(tenant_ctx.tenant.id) != tenant_id:
        raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="tenant_context_mismatch", message="租户上下文不匹配")
    payload_data = payload.model_copy(update={"tenant_id": tenant_id})
    try:
        subscription = service.create_subscription(db, payload_data)
        return TenantSubscriptionRead.model_validate(subscription)
    except ValidationError as exc:
        raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="validation_error", message=str(exc)) from exc


@router.get("", response_model=PaginatedResponse[TenantSubscriptionRead])
def list_subscriptions(
    tenant_id: str,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db_session),
    service: TenantSubscriptionService = Depends(tenant_subscription_service),
    tenant_ctx: TenantContext = Depends(require_permissions("tenant:subscription:manage")),
) -> PaginatedResponse[TenantSubscriptionRead]:
    if str(tenant_ctx.tenant.id) != tenant_id:
        raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="tenant_context_mismatch", message="租户上下文不匹配")
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
    tenant_ctx: TenantContext = Depends(require_permissions("tenant:subscription:manage")),
) -> TenantSubscriptionRead:
    if str(tenant_ctx.tenant.id) != tenant_id:
        raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="tenant_context_mismatch", message="租户上下文不匹配")
    try:
        subscription = service.get_subscription(db, subscription_id)
        if str(subscription.tenant_id) != tenant_id:
            raise ApiError(status_code=status.HTTP_404_NOT_FOUND, code="subscription_not_found", message="订阅不存在")
        return TenantSubscriptionRead.model_validate(subscription)
    except NotFoundError as exc:
        raise ApiError(status_code=status.HTTP_404_NOT_FOUND, code="not_found", message=str(exc)) from exc


@router.patch("/{subscription_id}", response_model=TenantSubscriptionRead)
def update_subscription(
    tenant_id: str,
    subscription_id: str,
    payload: TenantSubscriptionUpdate,
    db: Session = Depends(get_db_session),
    service: TenantSubscriptionService = Depends(tenant_subscription_service),
    tenant_ctx: TenantContext = Depends(require_permissions("tenant:subscription:manage")),
) -> TenantSubscriptionRead:
    if str(tenant_ctx.tenant.id) != tenant_id:
        raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="tenant_context_mismatch", message="租户上下文不匹配")
    try:
        subscription = service.update_subscription(db, subscription_id, payload)
        if str(subscription.tenant_id) != tenant_id:
            raise ApiError(status_code=status.HTTP_404_NOT_FOUND, code="subscription_not_found", message="订阅不存在")
        return TenantSubscriptionRead.model_validate(subscription)
    except NotFoundError as exc:
        raise ApiError(status_code=status.HTTP_404_NOT_FOUND, code="not_found", message=str(exc)) from exc
    except ValidationError as exc:
        raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="validation_error", message=str(exc)) from exc
