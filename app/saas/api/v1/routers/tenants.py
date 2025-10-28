"""租户管理路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.saas.api.v1.api_error import ApiError
from app.saas.api.v1.dependencies import (
    get_db_session,
    tenant_service,
)
from app.saas.schemas.common import PaginatedResponse
from app.saas.schemas.tenants import (
    TenantCreate,
    TenantPlanUpdate,
    TenantRead,
    TenantStatusUpdate,
    TenantUpdate,
)
from app.saas.services.exceptions import ConflictError, NotFoundError
from app.saas.services.pagination import PaginationParams
from app.saas.services.tenants.service import TenantService
from app.saas.models.tenant import TenantStatus

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
def create_tenant(
    payload: TenantCreate,
    db: Session = Depends(get_db_session),
    service: TenantService = Depends(tenant_service),
) -> TenantRead:
    try:
        tenant = service.create_tenant(db, payload)
        return TenantRead.model_validate(tenant)
    except ConflictError as exc:
        raise ApiError(status_code=status.HTTP_409_CONFLICT, code="tenant_already_exists", message=str(exc)) from exc


@router.get("", response_model=PaginatedResponse[TenantRead])
def list_tenants(
    page: int = 1,
    size: int = 20,
    status_filter: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db_session),
    service: TenantService = Depends(tenant_service),
) -> PaginatedResponse[TenantRead]:
    params = PaginationParams(page=page, size=size)
    status_enum: TenantStatus | None = None
    if status_filter:
        try:
            status_enum = TenantStatus[status_filter.upper()]
        except KeyError:
            raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="invalid_status_filter", message="无效的状态过滤器")
    result = service.list_tenants(db, params, status=status_enum, search=search)
    return PaginatedResponse[TenantRead](
        items=[TenantRead.model_validate(item) for item in result.items],
        meta=result.meta,
    )


@router.get("/{tenant_id}", response_model=TenantRead)
def get_tenant(
    tenant_id: str,
    db: Session = Depends(get_db_session),
    service: TenantService = Depends(tenant_service),
) -> TenantRead:
    try:
        tenant = service.get_tenant(db, tenant_id)
        return TenantRead.model_validate(tenant)
    except NotFoundError as exc:
        raise ApiError(status_code=status.HTTP_404_NOT_FOUND, code="not_found", message=str(exc)) from exc


@router.patch("/{tenant_id}", response_model=TenantRead)
def update_tenant(
    tenant_id: str,
    payload: TenantUpdate,
    db: Session = Depends(get_db_session),
    service: TenantService = Depends(tenant_service),
) -> TenantRead:
    try:
        tenant = service.update_tenant(db, tenant_id, payload)
        return TenantRead.model_validate(tenant)
    except NotFoundError as exc:
        raise ApiError(status_code=status.HTTP_404_NOT_FOUND, code="not_found", message=str(exc)) from exc


@router.post("/{tenant_id}/status", response_model=TenantRead)
def update_tenant_status(
    tenant_id: str,
    payload: TenantStatusUpdate,
    db: Session = Depends(get_db_session),
    service: TenantService = Depends(tenant_service),
) -> TenantRead:
    try:
        tenant = service.update_status(db, tenant_id, status=payload.status)
        return TenantRead.model_validate(tenant)
    except NotFoundError as exc:
        raise ApiError(status_code=status.HTTP_404_NOT_FOUND, code="not_found", message=str(exc)) from exc


@router.post("/{tenant_id}/plan", response_model=TenantRead)
def update_tenant_plan(
    tenant_id: str,
    payload: TenantPlanUpdate,
    db: Session = Depends(get_db_session),
    service: TenantService = Depends(tenant_service),
) -> TenantRead:
    try:
        tenant = service.update_plan(db, tenant_id, payload)
        return TenantRead.model_validate(tenant)
    except NotFoundError as exc:
        raise ApiError(status_code=status.HTTP_404_NOT_FOUND, code="not_found", message=str(exc)) from exc
