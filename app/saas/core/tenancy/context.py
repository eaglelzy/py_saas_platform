"""ContextVar backed tenant context container."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional

from app.saas.models.tenant import Tenant
from app.saas.models.tenant_member import TenantMember, TenantMemberRole
from app.saas.models.user import User


_active_tenant_id: ContextVar[Optional[str]] = ContextVar("active_tenant_id", default=None)


@dataclass(slots=True)
class TenantContext:
    """Carries tenant, user and membership references within a request."""

    tenant: Tenant
    user: User
    member: TenantMember
    role: TenantMemberRole

    @staticmethod
    def set_active_tenant_id(tenant_id: Optional[str]) -> None:
        _active_tenant_id.set(tenant_id)

    @staticmethod
    def get_active_tenant_id() -> Optional[str]:
        return _active_tenant_id.get()

    @staticmethod
    def reset() -> None:
        _active_tenant_id.set(None)


__all__ = ("TenantContext",)

