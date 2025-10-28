"""认证相关路由。"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.saas.api.v1.api_error import ApiError
from app.saas.api.v1.dependencies import (
    activation_token_service,
    audit_service,
    consultant_registration_service,
    get_current_user,
    get_db_session,
    notification_service,
    rate_limiter_service,
    refresh_token_service,
    token_blacklist_service,
    verification_code_service,
)
from app.saas.core.config.settings import settings
from app.saas.core.security.jwt import create_access_token
from app.saas.core.security.password import get_password_hash, verify_password
from app.saas.models.user import User
from app.saas.schemas.auth import (
    AccountActivationRequest,
    ActivationResponse,
    AuthLoginRequest,
    AuthTokenPair,
    AuthenticatedResponse,
    ConsultantRegisterRequest,
    ConsultantRegisterResponse,
    LogoutRequest,
    PasswordChangeRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenRefreshRequest,
    VerifyRegisterRequest,
)
from app.saas.schemas.common import SuccessResponse
from app.saas.schemas.users import UserRead
from app.saas.services.auth.activation_service import ActivationTokenService
from app.saas.services.auth.registration_service import ConsultantRegistrationService
from app.saas.services.auth.refresh_service import RefreshTokenService
from app.saas.services.auth.token_blacklist_service import TokenBlacklistService
from app.saas.services.audit import AuditService
from app.saas.services.exceptions import ConflictError, ValidationError, RateLimitExceededError
from app.saas.services.notifications import NotificationService
from app.saas.services.security import RateLimiterService
from app.saas.services.verification import VerificationService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register/verify", status_code=status.HTTP_200_OK)
def verify_register(
    payload: VerifyRegisterRequest,
    request: Request,
    verifier: VerificationService = Depends(verification_code_service),
) -> SuccessResponse:
    code = verifier.issue(scene="auth_register", target=payload.email)
    # TODO: 发送验证码到邮箱
    return SuccessResponse(message=f"验证码发送成功，验证码为：{code}")


@router.post("/register", response_model=SuccessResponse(message="顾问注册成功"), status_code=status.HTTP_201_CREATED)
def register_consultant(
    payload: ConsultantRegisterRequest,
    request: Request,
    db: Session = Depends(get_db_session),
    verifier: VerificationService = Depends(verification_code_service),
    limiter: RateLimiterService = Depends(rate_limiter_service),
    registration_svc: ConsultantRegistrationService = Depends(consultant_registration_service),
    notifier: NotificationService = Depends(notification_service),
    audit: AuditService = Depends(audit_service),
) -> ConsultantRegisterResponse:
    """顾问自助注册，初始化个人租户与默认订阅。"""

    identifier = payload.email
    if request and request.client:
        identifier = request.client.host or identifier
    try:
        limiter.check(scope="auth_register", identifier=identifier)
    except RateLimitExceededError as exc:
        raise ApiError(status_code=exc.status_code, code=exc.code, message=str(exc), detail=exc.context) from exc

    try:
        verifier.validate(scene="auth_register", target=payload.email, code=payload.verification_code)
    except ValidationError as exc:
        raise ApiError(status_code=exc.status_code, code=exc.code, message=str(exc)) from exc

    try:
        user, tenant, _subscription = registration_svc.register(db, payload)
    except ConflictError as exc:
        raise ApiError(status_code=exc.status_code, code=exc.code, message=str(exc)) from exc

    notifier.send_consultant_welcome(email=user.email, tenant_name=tenant.name)
    audit.log_event(
        db,
        user_id=str(user.id),
        tenant_id=str(tenant.id),
        action="consultant_registered",
        metadata={
            "email": user.email,
            "tenant_slug": tenant.slug,
        },
    )

@router.post("/login", response_model=AuthenticatedResponse)
def login(
    request: Request,
    payload: AuthLoginRequest,
    db: Session = Depends(get_db_session),
    refresh_svc: RefreshTokenService = Depends(refresh_token_service),
    blacklist: TokenBlacklistService = Depends(token_blacklist_service),
    audit: AuditService = Depends(audit_service),
) -> AuthenticatedResponse:
    stmt = select(User).where(User.email == payload.email)
    user = db.execute(stmt).scalars().first()
    if not user or not verify_password(payload.password, user.hashed_password):
        if user:
            user.failed_login_attempts += 1
            db.add(user)
            db.commit()
        raise ApiError(status_code=status.HTTP_401_UNAUTHORIZED, code="auth_login_failed", message="账号或密码错误")
    if not user.is_active or user.is_locked:
        raise ApiError(status_code=status.HTTP_403_FORBIDDEN, code="forbidden_account", message="账号不可用")

    user.failed_login_attempts = 0
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()

    access_token = create_access_token(str(user.id))
    refresh_token = refresh_svc.issue(
        db,
        user=user,
        user_agent=request.headers.get("user-agent") if request else None,
        ip_address=request.client.host if request and request.client else None,
    )
    blacklist.bind_refresh_session(str(user.id), refresh_token)

    expires_in = settings.access_token_expire_minutes * 60
    token_pair = AuthTokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )

    audit.log_event(
        db,
        user_id=str(user.id),
        action="login",
        metadata={"ip": request.client.host if request and request.client else None},
    )

    return AuthenticatedResponse(token=token_pair, user=UserRead.model_validate(user))


@router.post("/refresh", response_model=AuthTokenPair)
def refresh_token(
    payload: TokenRefreshRequest,
    db: Session = Depends(get_db_session),
    refresh_svc: RefreshTokenService = Depends(refresh_token_service),
) -> AuthTokenPair:
    try:
        record = refresh_svc.verify(db, payload.refresh_token)
    except ValidationError as exc:
        raise ApiError(status_code=status.HTTP_401_UNAUTHORIZED, code="validation_error", message=str(exc)) from exc

    access_token = create_access_token(str(record.user_id))
    expires_in = settings.access_token_expire_minutes * 60
    return AuthTokenPair(access_token=access_token, refresh_token=payload.refresh_token, expires_in=expires_in)


@router.post("/logout")
def logout(
    payload: LogoutRequest,
    db: Session = Depends(get_db_session),
    refresh_svc: RefreshTokenService = Depends(refresh_token_service),
    blacklist: TokenBlacklistService = Depends(token_blacklist_service),
    current_user: User = Depends(get_current_user),
    audit: AuditService = Depends(audit_service),
) -> dict[str, str]:
    if payload.refresh_token:
        refresh_svc.revoke(db, payload.refresh_token)
    blacklist.revoke_refresh_session(str(current_user.id))
    audit.log_event(db, user_id=str(current_user.id), action="logout")
    return {"detail": "已退出登录"}


@router.post("/activate", response_model=ActivationResponse)
def activate_account(
    payload: AccountActivationRequest,
    db: Session = Depends(get_db_session),
    activation_svc: ActivationTokenService = Depends(activation_token_service),
    audit: AuditService = Depends(audit_service),
) -> ActivationResponse:
    try:
        activation = activation_svc.get_valid_token(db, token=payload.token, purpose="activation")
    except ValidationError as exc:
        raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="validation_error", message=str(exc)) from exc

    user = db.get(User, activation.user_id)
    if user is None:
        raise ApiError(status_code=status.HTTP_404_NOT_FOUND, code="user_not_found", message="用户不存在")

    user.hashed_password = get_password_hash(payload.password)
    user.is_active = True
    user.is_locked = False
    user.password_updated_at = datetime.now(timezone.utc)
    user.failed_login_attempts = 0

    activation_svc.mark_used(db, activation)
    db.add(user)
    db.commit()
    db.refresh(user)

    audit.log_event(
        db,
        user_id=str(user.id),
        action="account_activated",
        metadata={"activation_token": payload.token},
    )

    return ActivationResponse()


@router.post("/password/change",
    response_model=SuccessResponse(message="密码修改成功，请重新登录"),
    status_code=status.HTTP_200_OK,
)
def change_password(
    payload: PasswordChangeRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    refresh_svc: RefreshTokenService = Depends(refresh_token_service),
    audit: AuditService = Depends(audit_service),
) -> dict[str, str]:
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="current_password_error", message="当前密码错误")
    current_user.hashed_password = get_password_hash(payload.new_password)
    current_user.password_updated_at = datetime.now(timezone.utc)
    db.add(current_user)
    db.commit()

    refresh_svc.revoke_user_tokens(db, current_user)
    audit.log_event(db, user_id=str(current_user.id), action="password_changed")


@router.post("/password/reset/request", 
    response_model=SuccessResponse(message="我们会发送重置邮件已发送到您的邮箱"),
    status_code=status.HTTP_200_OK,
)
def request_password_reset(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db_session),
    activation_svc: ActivationTokenService = Depends(activation_token_service),
    notifier: NotificationService = Depends(notification_service),
) -> dict[str, str]:
    stmt = select(User).where(User.email == payload.email)
    user = db.execute(stmt).scalars().first()
    if not user:
        raise ApiError(status_code=status.HTTP_404_NOT_FOUND, code="user_not_found", message="用户不存在")

    token_record = activation_svc.create_or_refresh(db, user=user, purpose="reset_password")
    reset_url = f"{settings.frontend_password_reset_url}?token={token_record.token}"
    notifier.send_password_reset(email=user.email, reset_url=reset_url)


@router.post("/password/reset/confirm",
    response_model=SuccessResponse(message="密码重置成功，请使用新密码登录"),
    status_code=status.HTTP_200_OK,
)
def confirm_password_reset(
    payload: PasswordResetConfirm,
    db: Session = Depends(get_db_session),
    activation_svc: ActivationTokenService = Depends(activation_token_service),
    refresh_svc: RefreshTokenService = Depends(refresh_token_service),
    audit: AuditService = Depends(audit_service),
) -> dict[str, str]:
    try:
        token_record = activation_svc.get_valid_token(db, token=payload.token, purpose="reset_password")
    except ValidationError as exc:
        raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="validation_error", message=str(exc)) from exc

    user = db.get(User, token_record.user_id)
    if not user:
        raise ApiError(status_code=status.HTTP_404_NOT_FOUND, code="user_not_found", message="用户不存在")

    user.hashed_password = get_password_hash(payload.password)
    user.password_updated_at = datetime.now(timezone.utc)
    user.failed_login_attempts = 0
    db.add(user)
    activation_svc.mark_used(db, token_record)
    db.commit()

    refresh_svc.revoke_user_tokens(db, user)
    audit.log_event(db, user_id=str(user.id), action="password_reset")
