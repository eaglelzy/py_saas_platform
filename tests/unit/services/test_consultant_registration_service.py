"""ConsultantRegistrationService 单元测试。"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.saas.schemas.auth import ConsultantRegisterRequest
from app.saas.services.auth.registration_service import ConsultantRegistrationService
from app.saas.services.exceptions import ConflictError
from app.saas.models.tenant import Tenant
from app.saas.models.tenant_subscription import TenantSubscription
from app.saas.models.user import User


@pytest.fixture()
def registration_service() -> ConsultantRegistrationService:
    return ConsultantRegistrationService()


def _build_payload(email_suffix: str = "001") -> ConsultantRegisterRequest:
    return ConsultantRegisterRequest(
        email=f"consultant_{email_suffix}@example.com",
        password="StrongPass1",
        verification_code="123456",
        full_name="Alice Consultant",
        display_name="Alice",
        workspace_name="Alice Studio",
        phone_number="+8613000000011",
        service_country="US",
        experience_years=5,
        timezone="Asia/Shanghai",
    )


def test_register_creates_user_tenant_and_subscription(
    db_session: Session,
    registration_service: ConsultantRegistrationService,
) -> None:
    payload = _build_payload()

    user, tenant, subscription = registration_service.register(db_session, payload)

    assert isinstance(user, User)
    assert isinstance(tenant, Tenant)
    assert isinstance(subscription, TenantSubscription)

    stored_user = db_session.get(User, user.id)
    stored_tenant = db_session.get(Tenant, tenant.id)
    stored_subscription = db_session.get(TenantSubscription, subscription.id)

    assert stored_user is not None
    assert stored_user.email == payload.email
    assert stored_tenant is not None
    assert stored_tenant.primary_owner_id == stored_user.id
    assert stored_tenant.member_limit == 1
    assert stored_subscription is not None
    assert stored_subscription.tenant_id == stored_tenant.id


def test_register_duplicate_email_raises_conflict(
    db_session: Session,
    registration_service: ConsultantRegistrationService,
) -> None:
    payload = _build_payload("dup")

    registration_service.register(db_session, payload)

    with pytest.raises(ConflictError):
        registration_service.register(db_session, payload)
