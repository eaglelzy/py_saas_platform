"""租户成员与邀请路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.saas.api.v1.api_error import ApiError
from app.saas.api.v1.dependencies import (
    get_db_session,
    member_invitation_service,
    tenant_member_service,
    notification_service,
    audit_service,
    require_permissions,
)
from app.saas.core.tenancy import TenantContext
from app.saas.schemas.common import PaginatedResponse
from app.saas.schemas.members import (
    InvitationAcceptRequest,
    InvitationAcceptResponse,
    MemberInvitationCreate,
    MemberInvitationRead,
    TenantMemberCreate,
    TenantMemberRead,
    TenantMemberUpdate,
)
from app.saas.services.exceptions import ConflictError, NotFoundError, ValidationError
from app.saas.services.members.service import MemberInvitationService, TenantMemberService
from app.saas.services.pagination import PaginationParams
from app.saas.models.member_invitation import InvitationStatus
from app.saas.models.tenant_member import TenantMemberStatus

router = APIRouter(prefix="/tenants/{tenant_id}", tags=["tenant-members"])


@router.post("/members", response_model=TenantMemberRead, status_code=status.HTTP_201_CREATED)
def add_member(
    tenant_id: str,
    payload: TenantMemberCreate,
    db: Session = Depends(get_db_session),
    service: TenantMemberService = Depends(tenant_member_service),
    tenant_ctx: TenantContext = Depends(require_permissions("tenant:member:manage")),
) -> TenantMemberRead:
    if str(tenant_ctx.tenant.id) != tenant_id:
        raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="tenant_context_mismatch", message="租户上下文不匹配")
    try:
        member = service.add_member(db, tenant_id, payload)
        return TenantMemberRead.model_validate(member)
    except (ConflictError, ValidationError) as exc:
        raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="validation_error", message=str(exc)) from exc


@router.get("/members", response_model=PaginatedResponse[TenantMemberRead])
def list_members(
    tenant_id: str,
    page: int = 1,
    size: int = 20,
    status_filter: str | None = None,
    db: Session = Depends(get_db_session),
    service: TenantMemberService = Depends(tenant_member_service),
    tenant_ctx: TenantContext = Depends(require_permissions("tenant:setting:view")),
) -> PaginatedResponse[TenantMemberRead]:
    if str(tenant_ctx.tenant.id) != tenant_id:
        raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="tenant_context_mismatch", message="租户上下文不匹配")
    params = PaginationParams(page=page, size=size)
    status_enum: TenantMemberStatus | None = None
    if status_filter:
        try:
            status_enum = TenantMemberStatus[status_filter.upper()]
        except KeyError:
            raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="invalid_status_filter", message="无效的状态过滤器")
    result = service.list_members(db, tenant_id, params, status=status_enum)
    return PaginatedResponse[TenantMemberRead](
        items=[TenantMemberRead.model_validate(item) for item in result.items],
        meta=result.meta,
    )


@router.patch("/members/{member_id}", response_model=TenantMemberRead)
def update_member(
    tenant_id: str,
    member_id: str,
    payload: TenantMemberUpdate,
    db: Session = Depends(get_db_session),
    service: TenantMemberService = Depends(tenant_member_service),
    tenant_ctx: TenantContext = Depends(require_permissions("tenant:member:manage")),
) -> TenantMemberRead:
    if str(tenant_ctx.tenant.id) != tenant_id:
        raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="tenant_context_mismatch", message="租户上下文不匹配")
    try:
        member = service.update_member(db, tenant_id, member_id, payload)
        return TenantMemberRead.model_validate(member)
    except NotFoundError as exc:
        raise ApiError(status_code=status.HTTP_404_NOT_FOUND, code="not_found", message=str(exc)) from exc


@router.delete("/members/{member_id}", response_model=TenantMemberRead)
def remove_member(
    tenant_id: str,
    member_id: str,
    db: Session = Depends(get_db_session),
    service: TenantMemberService = Depends(tenant_member_service),
    tenant_ctx: TenantContext = Depends(require_permissions("tenant:member:manage")),
) -> TenantMemberRead:
    if str(tenant_ctx.tenant.id) != tenant_id:
        raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="tenant_context_mismatch", message="租户上下文不匹配")
    try:
        member = service.remove_member(db, tenant_id, member_id)
        return TenantMemberRead.model_validate(member)
    except NotFoundError as exc:
        raise ApiError(status_code=status.HTTP_404_NOT_FOUND, code="not_found", message=str(exc)) from exc


@router.post("/invitations", response_model=MemberInvitationRead, status_code=status.HTTP_201_CREATED)
def create_invitation(
    tenant_id: str,
    payload: MemberInvitationCreate,
    db: Session = Depends(get_db_session),
    service: MemberInvitationService = Depends(member_invitation_service),
    notifier = Depends(notification_service),
    audit = Depends(audit_service),
    tenant_ctx: TenantContext = Depends(require_permissions("tenant:member:manage")),
) -> MemberInvitationRead:
    if str(tenant_ctx.tenant.id) != tenant_id:
        raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="tenant_context_mismatch", message="租户上下文不匹配")
    try:
        invitation = service.create_invitation(
            db,
            tenant_id,
            payload,
            notifier=notifier,
            audit_service=audit,
            invited_by_id=str(tenant_ctx.user.id),
        )
        return MemberInvitationRead.model_validate(invitation)
    except (ConflictError, ValidationError) as exc:
        raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="validation_error", message=str(exc)) from exc


@router.get("/invitations", response_model=PaginatedResponse[MemberInvitationRead])
def list_invitations(
    tenant_id: str,
    page: int = 1,
    size: int = 20,
    status_filter: str | None = None,
    db: Session = Depends(get_db_session),
    service: MemberInvitationService = Depends(member_invitation_service),
    tenant_ctx: TenantContext = Depends(require_permissions("tenant:member:manage")),
) -> PaginatedResponse[MemberInvitationRead]:
    if str(tenant_ctx.tenant.id) != tenant_id:
        raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="tenant_context_mismatch", message="租户上下文不匹配")
    params = PaginationParams(page=page, size=size)
    status_enum: InvitationStatus | None = None
    if status_filter:
        try:
            status_enum = InvitationStatus[status_filter.upper()]
        except KeyError:
            raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="invalid_status_filter", message="无效的状态过滤器")
    result = service.list_invitations(db, tenant_id, params, status=status_enum)
    return PaginatedResponse[MemberInvitationRead](
        items=[MemberInvitationRead.model_validate(item) for item in result.items],
        meta=result.meta,
    )


@router.post("/invitations/{token}/revoke", response_model=MemberInvitationRead)
def revoke_invitation(
    tenant_id: str,
    token: str,
    db: Session = Depends(get_db_session),
    service: MemberInvitationService = Depends(member_invitation_service),
    tenant_ctx: TenantContext = Depends(require_permissions("tenant:member:manage")),
) -> MemberInvitationRead:
    if str(tenant_ctx.tenant.id) != tenant_id:
        raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="tenant_context_mismatch", message="租户上下文不匹配")
    try:
        invitation = service.revoke_invitation(db, token)
        return MemberInvitationRead.model_validate(invitation)
    except NotFoundError as exc:
        raise ApiError(status_code=status.HTTP_404_NOT_FOUND, code="not_found", message=str(exc)) from exc
    except ValidationError as exc:
        raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="validation_error", message=str(exc)) from exc


@router.post("/invitations/{token}/accept", response_model=InvitationAcceptResponse)
def accept_invitation(
    tenant_id: str,
    token: str,
    request: InvitationAcceptRequest,
    db: Session = Depends(get_db_session),
    service: MemberInvitationService = Depends(member_invitation_service),
    audit = Depends(audit_service),
) -> InvitationAcceptResponse:
    try:
        response = service.accept_invitation(
            db,
            token,
            request=request,
            audit_service=audit,
            expected_tenant_id=tenant_id,
        )
        return response
    except NotFoundError as exc:
        raise ApiError(status_code=status.HTTP_404_NOT_FOUND, code="not_found", message=str(exc)) from exc
    except (ValidationError, ConflictError) as exc:
        raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="validation_error", message=str(exc)) from exc
