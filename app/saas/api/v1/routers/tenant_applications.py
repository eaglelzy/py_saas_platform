"""租户申请相关路由。

提供租户入驻申请的完整 API 接口：
- 企业提交申请
- 平台管理员查看申请列表（支持分页和状态过滤）
- 获取申请详情
- 审核申请（通过/驳回）
"""

from __future__ import annotations
from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.saas.api.v1.api_error import ApiError
from app.saas.api.v1.dependencies import (
    get_db_session,
    tenant_application_service,
    tenant_service,
    notification_service,
    activation_token_service,
)
from app.saas.schemas.applications import TenantApplicationRead, TenantApplicationReview, TenantApplicationSubmit
from app.saas.schemas.common import PaginatedResponse
from app.saas.services.exceptions import ServiceError, NotFoundError, ValidationError
from app.saas.services.pagination import PaginationParams
from app.saas.services.tenants.service import TenantApplicationService, TenantService
from app.saas.services.notifications import NotificationService
from app.saas.services.auth.activation_service import ActivationTokenService
from app.saas.models.tenant_application import ApplicationStatus

router = APIRouter(prefix="/tenant-applications", tags=["tenant-applications"])


@router.post("", response_model=TenantApplicationRead, status_code=status.HTTP_201_CREATED)
def submit_application(
    payload: TenantApplicationSubmit,
    db: Session = Depends(get_db_session),
    service: TenantApplicationService = Depends(tenant_application_service),
) -> TenantApplicationRead:
    """企业提交入驻申请。"""
    application = service.submit(db, payload)
    return TenantApplicationRead.model_validate(application)


@router.get("", response_model=PaginatedResponse[TenantApplicationRead])
def list_applications(
    page: int = Query(default=1, ge=1, description="页码, 从1开始"),
    size: int = Query(default=20, ge=1, le=100, description="每页条数, 范围1-100"),
    status_filter: Optional[ApplicationStatus] = Query(default=None, description="申请状态过滤"),
    db: Session = Depends(get_db_session),
    service: TenantApplicationService = Depends(tenant_application_service),
) -> PaginatedResponse[TenantApplicationRead]:
    """获取申请列表，支持分页和状态过滤。"""
    params = PaginationParams(page=page, size=size)
    status_enum: ApplicationStatus | None = None
    if status_filter:
        status_enum = ApplicationStatus[status_filter.upper()]
    result = service.list_applications(db, params, status=status_enum)
    return PaginatedResponse[TenantApplicationRead](
        items=[TenantApplicationRead.model_validate(item) for item in result.items],
        meta=result.meta,
    )


@router.get("/{application_id}", response_model=TenantApplicationRead)
def get_application(
    application_id: str,
    db: Session = Depends(get_db_session),
    service: TenantApplicationService = Depends(tenant_application_service),
) -> TenantApplicationRead:
    """获取单个申请详情。"""
    try:
        application = service.get(db, application_id)
        return TenantApplicationRead.model_validate(application)
    except NotFoundError as exc:
        raise ApiError(status_code=status.HTTP_404_NOT_FOUND, code="not_found", message=str(exc)) from exc


@router.post("/{application_id}/review", response_model=TenantApplicationRead)
def review_application(
    application_id: str,
    payload: TenantApplicationReview,
    db: Session = Depends(get_db_session),
    service: TenantApplicationService = Depends(tenant_application_service),
    tenant_svc: TenantService = Depends(tenant_service),
    notifier: NotificationService = Depends(notification_service),
    activation_svc: ActivationTokenService = Depends(activation_token_service),
) -> TenantApplicationRead:
    """审核申请（通过/驳回）。"""
    try:
        application = service.review(
            db,
            application_id,
            payload,
            tenant_service=tenant_svc,
            notification_service=notifier,
            activation_service=activation_svc,
        )
        return TenantApplicationRead.model_validate(application)
    except NotFoundError as exc:
        raise ApiError(status_code=status.HTTP_404_NOT_FOUND, code="not_found", message=str(exc)) from exc
    except ServiceError as exc:
        raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="validation_error", message=str(exc)) from exc
