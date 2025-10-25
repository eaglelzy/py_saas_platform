"""TenantService 核心行为测试。"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session
from uuid import uuid4

from app.models.user import User
from app.models.tenant import PlanCode, Tenant
from app.schemas.tenants import TenantCreate
from app.services.exceptions import ConflictError
from app.services.tenants.service import TenantService


@pytest.fixture()
def tenant_service() -> TenantService:
    return TenantService()


@pytest.fixture()
def primary_owner(db_session: Session) -> User:
    email = f"owner-{uuid4().hex[:8]}@example.com"
    user = User(
        email=email,
        hashed_password="hashed",
        display_name="Owner",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_create_tenant_success(db_session: Session, tenant_service: TenantService, primary_owner: User) -> None:
    payload = TenantCreate(
        name="Acme Corp",
        slug="ACME-CORP",
        primary_owner_id=str(primary_owner.id),
        plan_code=PlanCode.FREE,
        member_limit=5,
        contact_name="Alice",
        contact_email="alice@example.com",
        contact_phone="+8613000000000",
        timezone="Asia/Shanghai",
    )

    tenant = tenant_service.create_tenant(db_session, payload)

    assert isinstance(tenant, Tenant)
    assert tenant.name == "Acme Corp"
    assert tenant.slug == "acme-corp"  # slug 应被归一化为小写
    assert tenant.primary_owner_id == primary_owner.id
    assert tenant.plan_code == PlanCode.FREE
    assert tenant.member_limit == 5


def test_create_tenant_duplicate_slug(db_session: Session, tenant_service: TenantService, primary_owner: User) -> None:
    payload = TenantCreate(
        name="First",
        slug="duplicate",
        primary_owner_id=str(primary_owner.id),
        plan_code=PlanCode.FREE,
        member_limit=5,
        contact_name="Bob",
        contact_email="bob@example.com",
        contact_phone="+8613111111111",
        timezone="Asia/Shanghai",
    )
    tenant_service.create_tenant(db_session, payload)

    with pytest.raises(ConflictError):
        tenant_service.create_tenant(db_session, payload)
