"""Authentication and authorization helper utilities.

This module centralizes logic for extracting current users, tenants, and
performing permission checks. It complements the dependencies defined in
``app/api/v1/dependencies.py`` but avoids circular imports by exposing
functions that can be imported both in routes and reusable dependencies.
"""

from __future__ import annotations

from fastapi import Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.saas.api.v1.api_error import ApiError
from app.saas.core.logging import set_log_context
from app.saas.core.tenancy import TenantContext
from app.saas.core.tenancy.repository import PermissionCache, TenantContextRepository, get_permission_cache
from app.saas.db.session import get_db
from app.saas.models.user import User
from app.saas.services.auth.token_blacklist_service import TokenBlacklistService
from app.saas.core.config.settings import settings


bearer_scheme = HTTPBearer(auto_error=False)


def decode_current_user(
    credentials: HTTPAuthorizationCredentials | None,
    db: Session,
) -> User:
    """Decode JWT credentials, validate user and return the ORM object."""

    if credentials is None:
        raise ApiError(status_code=status.HTTP_401_UNAUTHORIZED, code="auth_missing_credentials", message="未提供凭证")

    from app.saas.core.security.jwt import decode_token  # avoid cyclic import

    try:
        payload = decode_token(credentials.credentials)
    except Exception as exc:  # noqa: BLE001
        raise ApiError(status_code=status.HTTP_401_UNAUTHORIZED, code="auth_invalid_token", message="无效的访问令牌", detail=str(exc)) from exc

    if payload.get("type") != "access":
        raise ApiError(status_code=status.HTTP_401_UNAUTHORIZED, code="auth_token_type_error", message="令牌类型错误")

    user_id = payload.get("sub")
    if not user_id:
        raise ApiError(status_code=status.HTTP_401_UNAUTHORIZED, code="auth_token_missing_sub", message="令牌缺少主体")

    user = db.get(User, user_id)
    if not user or not user.is_active or user.is_locked:
        raise ApiError(status_code=status.HTTP_401_UNAUTHORIZED, code="auth_account_inactive", message="账号不可用")

    # Persist tenant choice from token if present
    tenant_id = payload.get("tenant_id")
    if tenant_id:
        TenantContext.set_active_tenant_id(tenant_id)

    return user


def resolve_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    blacklist: TokenBlacklistService = Depends(lambda: TokenBlacklistService()),
) -> User:
    """FastAPI dependency to retrieve the current authenticated user."""

    user = decode_current_user(credentials, db)
    if credentials:
        token = credentials.credentials
        from jwt import decode as jwt_decode  # type: ignore
        try:
            payload = jwt_decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        except Exception as exc:  # noqa: BLE001
            raise ApiError(status_code=status.HTTP_401_UNAUTHORIZED, code="token_invalid", message="访问令牌已失效", detail=str(exc)) from exc
        jti = payload.get("jti")
        if jti and blacklist.is_access_token_blocked(jti):
            raise ApiError(status_code=status.HTTP_401_UNAUTHORIZED, code="token_invalid", message="访问令牌已失效")
    set_log_context(user_id=str(user.id))
    return user


def resolve_current_tenant(
    request: Request,
    current_user: User = Depends(resolve_current_user),
    db: Session = Depends(get_db),
    repo: TenantContextRepository = Depends(lambda: TenantContextRepository()),
) -> TenantContext:
    """Derive current tenant from header, query, or token and ensure membership."""

    header_tenant_id = request.headers.get("X-Tenant-ID")
    path_tenant_id = request.path_params.get("tenant_id") if hasattr(request, "path_params") else None

    tenant_id = header_tenant_id or path_tenant_id or TenantContext.get_active_tenant_id()
    if not tenant_id:
        raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="tenant_context_missing", message="缺少租户上下文")

    if header_tenant_id and path_tenant_id and header_tenant_id != path_tenant_id:
        raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="tenant_context_mismatch", message="租户上下文不一致")

    tenant_ctx = repo.ensure_membership(db, tenant_id=tenant_id, user=current_user)
    TenantContext.set_active_tenant_id(str(tenant_ctx.tenant.id))
    set_log_context(tenant_id=str(tenant_ctx.tenant.id))
    return tenant_ctx


def require_permissions(*permissions: str) -> callable:
    """Dependency factory enforcing that current user has all required permissions."""

    def dependency(
        tenant_ctx: TenantContext = Depends(resolve_current_tenant),
        cache: PermissionCache = Depends(get_permission_cache),
        db: Session = Depends(get_db),
    ) -> TenantContext:
        cache.assert_permissions(db, tenant_ctx=tenant_ctx, permissions=permissions)
        return tenant_ctx

    return dependency
