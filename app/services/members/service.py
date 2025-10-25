"""租户成员与邀请的业务逻辑。"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.core.config.settings import settings
from app.models.member_invitation import InvitationStatus, MemberInvitation
from app.models.tenant_member import TenantMember, TenantMemberStatus
from app.schemas.common import PaginatedResponse
from app.schemas.members import (
    InvitationAcceptRequest,
    InvitationAcceptResponse,
    MemberInvitationCreate,
    TenantMemberCreate,
    TenantMemberRead,
    TenantMemberUpdate,
)
from app.services.exceptions import ConflictError, NotFoundError, ValidationError
from app.services.members.repository import MemberInvitationRepository, TenantMemberRepository
from app.services.pagination import PaginationParams, build_paginated_response, paginate_stmt
from app.services.tenants.repository import TenantRepository


class TenantMemberService:
    """租户成员管理。"""

    def __init__(self) -> None:
        self.member_repo = TenantMemberRepository()
        self.tenant_repo = TenantRepository()

    def _ensure_quota(self, db: Session, *, tenant_id: str) -> None:
        tenant = self.tenant_repo.get_or_raise(db, id=tenant_id)
        active_members = self.member_repo.count_active(db, tenant_id=tenant_id)
        if active_members >= tenant.member_limit:
            raise ValidationError("成员数量已达上限，请升级套餐", code="member_limit_reached")

    def add_member(self, db: Session, tenant_id: str, payload: TenantMemberCreate) -> TenantMember:
        if self.member_repo.get_by_user(db, tenant_id=tenant_id, user_id=payload.user_id):
            raise ConflictError("成员已存在", code="member_exists")
        self._ensure_quota(db, tenant_id=tenant_id)
        data = payload.model_dump(exclude_unset=True)
        data["tenant_id"] = tenant_id
        member = self.member_repo.create(db, obj_in=data)
        db.commit()
        db.refresh(member)
        return member

    def list_members(
        self,
        db: Session,
        tenant_id: str,
        params: PaginationParams,
        *,
        status: Optional[TenantMemberStatus] = None,
    ) -> PaginatedResponse[TenantMember]:
        stmt: Select[tuple[TenantMember]] = select(TenantMember).where(TenantMember.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(TenantMember.status == status)
        stmt = stmt.order_by(TenantMember.created_at.desc())
        items, meta = paginate_stmt(db, stmt, params)
        return build_paginated_response(items, meta)

    def get_member(self, db: Session, tenant_id: str, member_id: str) -> TenantMember:
        member = self.member_repo.get_or_raise(db, id=member_id)
        if str(member.tenant_id) != tenant_id:
            raise NotFoundError("成员不属于该租户", code="member_tenant_mismatch")
        return member

    def update_member(
        self,
        db: Session,
        tenant_id: str,
        member_id: str,
        payload: TenantMemberUpdate,
    ) -> TenantMember:
        member = self.get_member(db, tenant_id, member_id)
        updated = self.member_repo.update(db, db_obj=member, obj_in=payload)
        db.commit()
        db.refresh(updated)
        return updated

    def remove_member(self, db: Session, tenant_id: str, member_id: str) -> TenantMember:
        member = self.get_member(db, tenant_id, member_id)
        member.status = TenantMemberStatus.REMOVED
        member.deactivated_at = datetime.now(timezone.utc)
        db.add(member)
        db.commit()
        db.refresh(member)
        return member


class MemberInvitationService:
    """成员邀请管理。"""

    def __init__(self) -> None:
        self.invite_repo = MemberInvitationRepository()
        self.member_repo = TenantMemberRepository()
        self.tenant_repo = TenantRepository()

    def _generate_token(self) -> str:
        return secrets.token_urlsafe(32)

    def _ensure_quota(self, db: Session, tenant_id: str) -> None:
        tenant = self.tenant_repo.get_or_raise(db, id=tenant_id)
        active_members = self.member_repo.count_active(db, tenant_id=tenant_id)
        pending_invites = len(self.invite_repo.list_pending(db, tenant_id=tenant_id))
        if active_members + pending_invites >= tenant.member_limit:
            raise ValidationError("成员或邀请数量已达到上限", code="member_limit_reached")

    def create_invitation(
        self,
        db: Session,
        tenant_id: str,
        payload: MemberInvitationCreate,
        *,
        invited_by_id: Optional[str] = None,
    ) -> MemberInvitation:
        pending_invites = self.invite_repo.list_pending(db, tenant_id=tenant_id)
        if any(inv.email == payload.email for inv in pending_invites):
            raise ConflictError("该邮箱已存在待处理邀请", code="invitation_exists")
        self._ensure_quota(db, tenant_id)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.invite_token_expire_hours)
        invitation_data = {
            "tenant_id": tenant_id,
            "invited_by_id": invited_by_id,
            "role": payload.role,
            "email": payload.email,
            "token": self._generate_token(),
            "status": InvitationStatus.PENDING,
            "expires_at": expires_at,
            "message": payload.message,
        }
        invitation = self.invite_repo.create(db, obj_in=invitation_data)
        db.commit()
        db.refresh(invitation)
        return invitation

    def get_invitation(self, db: Session, token: str) -> MemberInvitation:
        invitation = self.invite_repo.get_by_token(db, token=token)
        if not invitation:
            raise NotFoundError("邀请不存在", code="invitation_not_found")
        return invitation

    def list_invitations(
        self,
        db: Session,
        tenant_id: str,
        params: PaginationParams,
        *,
        status: Optional[InvitationStatus] = None,
    ) -> PaginatedResponse[MemberInvitation]:
        stmt: Select[tuple[MemberInvitation]] = select(MemberInvitation).where(MemberInvitation.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(MemberInvitation.status == status)
        stmt = stmt.order_by(MemberInvitation.created_at.desc())
        items, meta = paginate_stmt(db, stmt, params)
        return build_paginated_response(items, meta)

    def revoke_invitation(self, db: Session, token: str) -> MemberInvitation:
        invitation = self.get_invitation(db, token)
        if invitation.status != InvitationStatus.PENDING:
            raise ValidationError("仅待处理邀请可撤销", code="invitation_not_pending")
        invitation.status = InvitationStatus.REVOKED
        invitation.revoked_at = datetime.now(timezone.utc)
        db.add(invitation)
        db.commit()
        db.refresh(invitation)
        return invitation

    def accept_invitation(
        self,
        db: Session,
        token: str,
        *,
        user_id: str,
    ) -> InvitationAcceptResponse:
        invitation = self.get_invitation(db, token)
        if invitation.status != InvitationStatus.PENDING:
            raise ValidationError("邀请不可用", code="invitation_not_active")
        if invitation.expires_at and invitation.expires_at < datetime.now(timezone.utc):
            invitation.status = InvitationStatus.EXPIRED
            db.add(invitation)
            db.commit()
            raise ValidationError("邀请已过期", code="invitation_expired")

        member = self.member_repo.get_by_user(db, tenant_id=str(invitation.tenant_id), user_id=user_id)
        if member:
            if member.status == TenantMemberStatus.REMOVED:
                member.status = TenantMemberStatus.ACTIVE
                member.role = invitation.role
                member.activated_at = datetime.now(timezone.utc)
                db.add(member)
            else:
                raise ConflictError("用户已是成员", code="member_exists")
        else:
            self.tenant_repo.get_or_raise(db, id=str(invitation.tenant_id))
            member_data = {
                "tenant_id": str(invitation.tenant_id),
                "user_id": user_id,
                "role": invitation.role,
                "status": TenantMemberStatus.ACTIVE,
                "invited_by_id": invitation.invited_by_id,
                "activated_at": datetime.now(timezone.utc),
            }
            member = self.member_repo.create(db, obj_in=member_data)

        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = datetime.now(timezone.utc)
        db.add(invitation)
        db.commit()
        db.refresh(invitation)
        db.refresh(member)

        member_read = TenantMemberRead.model_validate(member)
        return InvitationAcceptResponse(member=member_read, tenant_id=str(invitation.tenant_id))
