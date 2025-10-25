"""Repositories to resolve tenant context and cache permissions."""

from __future__ import annotations

import time
from typing import Iterable, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config.settings import settings
from app.core.logging import logger
from app.core.tenancy import TenantContext
from app.models.tenant import TenantStatus
from app.models.tenant_member import TenantMember, TenantMemberRole, TenantMemberStatus
from app.models.tenant_permission import TenantRolePermission
from app.models.user import User
from app.services.tenants.repository import TenantRepository


class TenantContextRepository:
    """Ensure that a user can access the requested tenant and bind RLS."""

    def __init__(self, tenant_repo: TenantRepository | None = None) -> None:
        self.tenant_repo = tenant_repo or TenantRepository()

    def ensure_membership(self, db: Session, *, tenant_id: str, user: User) -> TenantContext:
        try:
            tenant_uuid = UUID(str(tenant_id))
        except (ValueError, TypeError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="租户标识无效")

        tenant = self.tenant_repo.get_or_raise(db, id=tenant_uuid)
        if tenant.status in {TenantStatus.SUSPENDED, TenantStatus.ARCHIVED}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="租户不可用")

        stmt = select(TenantMember).where(
            TenantMember.tenant_id == tenant.id,
            TenantMember.user_id == user.id,
        )
        member = db.execute(stmt).scalars().first()
        if member is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该租户")

        if member.status not in {TenantMemberStatus.ACTIVE, TenantMemberStatus.PENDING}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="成员状态不可用")

        bind = db.get_bind()
        if bind is not None and bind.dialect.name.startswith("postgres"):
            db.execute(text("SET LOCAL app.current_tenant = :tenant_id"), {"tenant_id": str(tenant.id)})
        logger.bind(component="tenant_context", tenant_id=str(tenant.id), user_id=str(user.id)).debug("绑定租户上下文")

        ctx = TenantContext(tenant=tenant, user=user, member=member, role=member.role)
        return ctx


class PermissionCache:
    """In-memory cache for role permissions with TTL."""

    def __init__(self) -> None:
        self._cache: dict[str, tuple[float, set[str]]] = {}
        self._ttl = settings.permission_cache_ttl_seconds

    def _cache_key(self, tenant_id: str, role: TenantMemberRole) -> str:
        return f"{tenant_id}:{role.value}"

    def get_permissions(self, db: Session, *, tenant_ctx: TenantContext) -> set[str]:
        key = self._cache_key(str(tenant_ctx.tenant.id), tenant_ctx.role)
        cached = self._cache.get(key)
        now = time.time()
        if cached and now - cached[0] < self._ttl:
            return cached[1]

        permissions = self._load_permissions(db, tenant_ctx)
        self._cache[key] = (now, permissions)
        return permissions

    def assert_permissions(
        self,
        db: Session,
        *,
        tenant_ctx: TenantContext,
        permissions: Iterable[str],
    ) -> None:
        granted = self.get_permissions(db, tenant_ctx=tenant_ctx)
        missing = [perm for perm in permissions if perm not in granted]
        if missing:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="缺少必要权限")

    def invalidate(self, tenant_id: str, role: TenantMemberRole | None = None) -> None:
        if role is None:
            prefix = f"{tenant_id}:"
            keys = [key for key in self._cache.keys() if key.startswith(prefix)]
            for key in keys:
                self._cache.pop(key, None)
            return
        self._cache.pop(self._cache_key(tenant_id, role), None)

    def _load_permissions(self, db: Session, tenant_ctx: TenantContext) -> set[str]:
        defaults = {
            TenantMemberRole.OWNER: set(settings.default_owner_permissions),
            TenantMemberRole.ADMIN: set(settings.default_admin_permissions),
            TenantMemberRole.MEMBER: set(settings.default_member_permissions),
        }[tenant_ctx.role]

        stmt = select(TenantRolePermission.permission).where(
            TenantRolePermission.tenant_id == tenant_ctx.tenant.id,
            TenantRolePermission.role == tenant_ctx.role.value,
        )
        extra = set(db.execute(stmt).scalars().all())
        return defaults | extra


_permission_cache = PermissionCache()


def get_permission_cache() -> PermissionCache:
    return _permission_cache


__all__ = ("TenantContextRepository", "PermissionCache", "get_permission_cache")
