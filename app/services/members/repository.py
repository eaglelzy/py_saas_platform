"""租户成员与邀请的仓储。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.member_invitation import InvitationStatus, MemberInvitation
from app.models.tenant_member import TenantMember, TenantMemberStatus
from app.services.base import CRUDRepository


class TenantMemberRepository(CRUDRepository[TenantMember]):
    """租户成员仓储。"""

    def __init__(self) -> None:
        super().__init__(TenantMember)

    def list_by_tenant(
        self,
        db: Session,
        *,
        tenant_id: str,
        status: Optional[TenantMemberStatus] = None,
    ) -> list[TenantMember]:
        stmt: Select[tuple[TenantMember]] = select(TenantMember).where(TenantMember.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(TenantMember.status == status)
        stmt = stmt.order_by(TenantMember.created_at.desc())
        return db.execute(stmt).scalars().all()

    def get_by_user(self, db: Session, *, tenant_id: str, user_id: str) -> Optional[TenantMember]:
        stmt = select(TenantMember).where(
            TenantMember.tenant_id == tenant_id,
            TenantMember.user_id == user_id,
        )
        return db.execute(stmt).scalars().first()

    def count_active(self, db: Session, *, tenant_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(TenantMember)
            .where(
                TenantMember.tenant_id == tenant_id,
                TenantMember.status.in_([TenantMemberStatus.PENDING, TenantMemberStatus.ACTIVE]),
            )
        )
        return db.execute(stmt).scalar_one()


class MemberInvitationRepository(CRUDRepository[MemberInvitation]):
    """成员邀请仓储。"""

    def __init__(self) -> None:
        super().__init__(MemberInvitation)

    def get_by_token(self, db: Session, *, token: str) -> Optional[MemberInvitation]:
        stmt = select(MemberInvitation).where(MemberInvitation.token == token)
        return db.execute(stmt).scalars().first()

    def list_pending(self, db: Session, *, tenant_id: str) -> list[MemberInvitation]:
        stmt = select(MemberInvitation).where(
            MemberInvitation.tenant_id == tenant_id,
            MemberInvitation.status == InvitationStatus.PENDING,
        )
        return db.execute(stmt).scalars().all()

    def mark_expired(self, db: Session, invitation: MemberInvitation) -> MemberInvitation:
        invitation.status = InvitationStatus.EXPIRED
        invitation.expires_at = invitation.expires_at or datetime.now(timezone.utc)
        db.add(invitation)
        return invitation
