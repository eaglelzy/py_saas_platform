"""订阅套餐路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_db_session, subscription_plan_service
from app.schemas.common import PaginatedResponse
from app.schemas.subscriptions import SubscriptionPlanCreate, SubscriptionPlanRead, SubscriptionPlanUpdate
from app.services.exceptions import ConflictError, NotFoundError
from app.services.pagination import PaginationParams
from app.services.subscriptions.service import SubscriptionPlanService

router = APIRouter(prefix="/subscription-plans", tags=["subscription-plans"])


@router.post("", response_model=SubscriptionPlanRead, status_code=status.HTTP_201_CREATED)
def create_plan(
    payload: SubscriptionPlanCreate,
    db: Session = Depends(get_db_session),
    service: SubscriptionPlanService = Depends(subscription_plan_service),
) -> SubscriptionPlanRead:
    try:
        plan = service.create_plan(db, payload)
        return SubscriptionPlanRead.model_validate(plan)
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("", response_model=PaginatedResponse[SubscriptionPlanRead])
def list_plans(
    page: int = 1,
    size: int = 20,
    only_active: bool = False,
    db: Session = Depends(get_db_session),
    service: SubscriptionPlanService = Depends(subscription_plan_service),
) -> PaginatedResponse[SubscriptionPlanRead]:
    params = PaginationParams(page=page, size=size)
    result = service.list_plans(db, params, only_active=only_active)
    return PaginatedResponse[SubscriptionPlanRead](
        items=[SubscriptionPlanRead.model_validate(item) for item in result.items],
        meta=result.meta,
    )


@router.get("/{plan_id}", response_model=SubscriptionPlanRead)
def get_plan(
    plan_id: str,
    db: Session = Depends(get_db_session),
    service: SubscriptionPlanService = Depends(subscription_plan_service),
) -> SubscriptionPlanRead:
    try:
        plan = service.get_plan(db, plan_id)
        return SubscriptionPlanRead.model_validate(plan)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{plan_id}", response_model=SubscriptionPlanRead)
def update_plan(
    plan_id: str,
    payload: SubscriptionPlanUpdate,
    db: Session = Depends(get_db_session),
    service: SubscriptionPlanService = Depends(subscription_plan_service),
) -> SubscriptionPlanRead:
    try:
        plan = service.update_plan(db, plan_id, payload)
        return SubscriptionPlanRead.model_validate(plan)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{plan_id}/toggle", response_model=SubscriptionPlanRead)
def toggle_plan(
    plan_id: str,
    is_active: bool,
    db: Session = Depends(get_db_session),
    service: SubscriptionPlanService = Depends(subscription_plan_service),
) -> SubscriptionPlanRead:
    try:
        plan = service.toggle_plan(db, plan_id, is_active=is_active)
        return SubscriptionPlanRead.model_validate(plan)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
