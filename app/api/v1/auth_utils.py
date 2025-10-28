"""Authentication and authorization helper utilities.

This module centralizes logic for extracting current users, tenants, and
performing permission checks. It complements the dependencies defined in
``app/api/v1/dependencies.py`` but avoids circular imports by exposing
functions that can be imported both in routes and reusable dependencies.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.logging import set_log_context
from app.core.tenancy import TenantContext
from app.core.tenancy.repository import PermissionCache, TenantContextRepository, get_permission_cache
from app.db.session import get_db
from app.models.user import User


bearer_scheme = HTTPBearer(auto_error=False)


def decode_current_user(
    credentials: HTTPAuthorizationCredentials | None,
    db: Session,
) -> User:
    """Decode JWT credentials, validate user and return the ORM object."""

    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未提供凭证")

    from app.core.security.jwt import decode_token  # avoid cyclic import

    try:
        payload = decode_token(credentials.credentials)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的访问令牌") from exc

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌类型错误")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌缺少主体")

    user = db.get(User, user_id)
    if not user or not user.is_active or user.is_locked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号不可用")

    # Persist tenant choice from token if present
    tenant_id = payload.get("tenant_id")
    if tenant_id:
        TenantContext.set_active_tenant_id(tenant_id)

    return user


def resolve_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency to retrieve the current authenticated user."""

    user = decode_current_user(credentials, db)
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="缺少租户上下文")

    if header_tenant_id and path_tenant_id and header_tenant_id != path_tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="租户上下文不一致")

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
