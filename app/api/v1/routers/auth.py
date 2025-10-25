"""认证相关路由。"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.dependencies import (
    get_db_session,
    activation_token_service,
    audit_service,
    refresh_token_service,
    get_current_user,
    notification_service,
)
from app.core.config.settings import settings
from app.core.security.password import get_password_hash, verify_password
from app.core.security.jwt import create_access_token
from app.models.user import User
from app.schemas.auth import (
    AccountActivationRequest,
    ActivationResponse,
    AuthLoginRequest,
    AuthenticatedResponse,
    AuthTokenPair,
    TokenRefreshRequest,
    LogoutRequest,
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from app.schemas.users import UserRead
from app.services.auth.activation_service import ActivationTokenService
from app.services.auth.refresh_service import RefreshTokenService
from app.services.audit import AuditService
from app.services.notifications import NotificationService
from app.services.exceptions import ValidationError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthenticatedResponse)
def login(
    payload: AuthLoginRequest,
    db: Session = Depends(get_db_session),
    refresh_svc: RefreshTokenService = Depends(refresh_token_service),
    audit: AuditService = Depends(audit_service),
    request: Request = Depends(),
) -> AuthenticatedResponse:
    stmt = select(User).where(User.email == payload.email)
    user = db.execute(stmt).scalars().first()
    if not user or not verify_password(payload.password, user.hashed_password):
        if user:
            user.failed_login_attempts += 1
            db.add(user)
            db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误")

    if not user.is_active or user.is_locked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号不可用")

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
    expires_in = settings.access_token_expire_minutes * 60
    token_pair = AuthTokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )

    audit.log_event(db, user_id=str(user.id), action="login", metadata={"ip": request.client.host if request and request.client else None})

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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    access_token = create_access_token(str(record.user_id))
    expires_in = settings.access_token_expire_minutes * 60
    return AuthTokenPair(access_token=access_token, refresh_token=payload.refresh_token, expires_in=expires_in)


@router.post("/logout")
def logout(
    payload: LogoutRequest,
    db: Session = Depends(get_db_session),
    refresh_svc: RefreshTokenService = Depends(refresh_token_service),
    current_user: User = Depends(get_current_user),
    audit: AuditService = Depends(audit_service),
) -> dict[str, str]:
    if payload.refresh_token:
        refresh_svc.revoke(db, payload.refresh_token)
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    user = db.get(User, activation.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

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


@router.post("/password/change")
def change_password(
    payload: PasswordChangeRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    refresh_svc: RefreshTokenService = Depends(refresh_token_service),
    audit: AuditService = Depends(audit_service),
) -> dict[str, str]:
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前密码错误")
    current_user.hashed_password = get_password_hash(payload.new_password)
    current_user.password_updated_at = datetime.now(timezone.utc)
    db.add(current_user)
    db.commit()

    refresh_svc.revoke_user_tokens(db, current_user)
    audit.log_event(db, user_id=str(current_user.id), action="password_changed")
    return {"detail": "密码修改成功，请重新登录"}


@router.post("/password/reset/request")
def request_password_reset(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db_session),
    activation_svc: ActivationTokenService = Depends(activation_token_service),
    notifier: NotificationService = Depends(notification_service),
) -> dict[str, str]:
    stmt = select(User).where(User.email == payload.email)
    user = db.execute(stmt).scalars().first()
    if not user:
        return {"detail": "如果邮箱存在，我们会发送重置邮件"}

    token_record = activation_svc.create_or_refresh(db, user=user, purpose="reset_password")
    reset_url = f"{settings.frontend_password_reset_url}?token={token_record.token}"
    notifier.send_password_reset(email=user.email, reset_url=reset_url)
    return {"detail": "如果邮箱存在，我们会发送重置邮件"}


@router.post("/password/reset/confirm")
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    user = db.get(User, token_record.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    user.hashed_password = get_password_hash(payload.password)
    user.password_updated_at = datetime.now(timezone.utc)
    user.failed_login_attempts = 0
    db.add(user)
    activation_svc.mark_used(db, token_record)
    db.commit()

    refresh_svc.revoke_user_tokens(db, user)
    audit.log_event(db, user_id=str(user.id), action="password_reset")

    return {"detail": "密码重置成功，请使用新密码登录"}
