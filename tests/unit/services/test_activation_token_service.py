"""ActivationTokenService 行为测试。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from uuid import uuid4

from app.models.user import User
from app.services.auth.activation_service import ActivationTokenService
from app.services.exceptions import ValidationError
from app.core.security.password import get_password_hash


@pytest.fixture()
def activation_service() -> ActivationTokenService:
    return ActivationTokenService()


@pytest.fixture()
def user(db_session: Session) -> User:
    user = User(
        email=f"activation-{uuid4().hex[:8]}@example.com",
        hashed_password=get_password_hash("TempPass123"),
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_create_and_validate_token(db_session: Session, activation_service: ActivationTokenService, user: User) -> None:
    token_record = activation_service.create_or_refresh(db_session, user=user)
    assert token_record.token

    queried = activation_service.get_valid_token(db_session, token=token_record.token)
    assert queried.id == token_record.id

    activation_service.mark_used(db_session, queried)
    db_session.commit()
    with pytest.raises(ValidationError):
        activation_service.get_valid_token(db_session, token=token_record.token)


def test_token_expired(db_session: Session, activation_service: ActivationTokenService, user: User) -> None:
    token_record = activation_service.create_or_refresh(db_session, user=user, purpose="reset_password")
    token_record.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.add(token_record)
    db_session.commit()

    with pytest.raises(ValidationError):
        activation_service.get_valid_token(db_session, token=token_record.token, purpose="reset_password")
