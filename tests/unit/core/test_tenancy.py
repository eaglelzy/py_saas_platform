"""Unit tests for tenancy context and permission utilities."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

import uuid

from app.core.tenancy import TenantContext
from app.core.tenancy.repository import PermissionCache, TenantContextRepository
from app.models.tenant import PlanCode, Tenant, TenantStatus
from app.models.tenant_member import TenantMember, TenantMemberRole, TenantMemberStatus
from app.models.tenant_permission import TenantRolePermission
from app.models.user import User


def _create_user() -> User:
    suffix = uuid.uuid4().hex[:8]
    return User(
        id=uuid.uuid4(),
        email=f"user_{suffix}@example.com",
        hashed_password="hashed",
        is_active=True,
        is_locked=False,
    )


def _create_tenant(owner_id: uuid.UUID) -> Tenant:
    suffix = uuid.uuid4().hex[:6]
    return Tenant(
        id=uuid.uuid4(),
        name=f"Tenant {suffix}",
        slug=f"tenant-{suffix}",
        primary_owner_id=owner_id,
        status=TenantStatus.ACTIVE,
        plan_code=PlanCode.FREE,
        member_limit=5,
        contact_name="Owner",
        contact_email="owner@example.com",
        contact_phone="123",
        timezone="UTC",
    )


def test_ensure_membership_active_member(db_session) -> None:
    repo = TenantContextRepository()
    user = _create_user()
    tenant = _create_tenant(user.id)
    member = TenantMember(
        tenant_id=tenant.id,
        user_id=user.id,
        role=TenantMemberRole.ADMIN,
        status=TenantMemberStatus.ACTIVE,
    )
    db_session.add_all([user, tenant, member])
    db_session.commit()

    ctx = repo.ensure_membership(db_session, tenant_id=str(tenant.id), user=user)

    assert ctx.tenant.id == tenant.id
    assert ctx.member.id == member.id
    assert ctx.role == TenantMemberRole.ADMIN


def test_ensure_membership_inactive_member(db_session) -> None:
    repo = TenantContextRepository()
    user = _create_user()
    tenant = _create_tenant(user.id)
    member = TenantMember(
        tenant_id=tenant.id,
        user_id=user.id,
        role=TenantMemberRole.ADMIN,
        status=TenantMemberStatus.SUSPENDED,
    )
    db_session.add_all([user, tenant, member])
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        repo.ensure_membership(db_session, tenant_id=str(tenant.id), user=user)

    assert exc.value.status_code == 403


def test_permission_cache_merges_defaults_and_custom(db_session) -> None:
    user = _create_user()
    tenant = _create_tenant(user.id)
    member = TenantMember(
        tenant_id=tenant.id,
        user_id=user.id,
        role=TenantMemberRole.ADMIN,
        status=TenantMemberStatus.ACTIVE,
    )
    custom_permission = TenantRolePermission(
        tenant_id=tenant.id,
        role=TenantMemberRole.ADMIN.value,
        permission="custom:feature",
    )
    db_session.add_all([user, tenant, member, custom_permission])
    db_session.commit()

    ctx = TenantContext(tenant=tenant, user=user, member=member, role=TenantMemberRole.ADMIN)
    cache = PermissionCache()

    permissions = cache.get_permissions(db_session, tenant_ctx=ctx)

    assert "tenant:member:manage" in permissions
    assert "custom:feature" in permissions

    cache.assert_permissions(db_session, tenant_ctx=ctx, permissions=["custom:feature"])

    with pytest.raises(HTTPException):
        cache.assert_permissions(db_session, tenant_ctx=ctx, permissions=["missing:perm"])
