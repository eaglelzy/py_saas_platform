"""激活 Token 的仓储操作。"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Select, delete, select
from sqlalchemy.orm import Session

from app.models.activation_token import ActivationToken
from app.services.base import CRUDRepository


def _normalize_uuid(value: str | uuid.UUID) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(value)


class ActivationTokenRepository(CRUDRepository[ActivationToken]):
    """提供激活 token 的查询与写入操作。"""

    def __init__(self) -> None:
        super().__init__(ActivationToken)

    def get_by_user(self, db: Session, *, user_id: str | uuid.UUID, purpose: str) -> Optional[ActivationToken]:
        stmt: Select[tuple[ActivationToken]] = select(ActivationToken).where(
            ActivationToken.user_id == _normalize_uuid(user_id),
            ActivationToken.purpose == purpose,
        )
        return db.execute(stmt).scalars().first()

    def get_by_token(self, db: Session, *, token: str, purpose: str) -> Optional[ActivationToken]:
        stmt: Select[tuple[ActivationToken]] = select(ActivationToken).where(
            ActivationToken.token == token,
            ActivationToken.purpose == purpose,
        )
        return db.execute(stmt).scalars().first()

    def delete_by_user(self, db: Session, *, user_id: str | uuid.UUID, purpose: str) -> None:
        stmt = delete(ActivationToken).where(
            ActivationToken.user_id == _normalize_uuid(user_id),
            ActivationToken.purpose == purpose,
        )
        db.execute(stmt)
