"""租户相关仓储实现。"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.models.tenant_application import ApplicationStatus, TenantApplication
from app.services.base import CRUDRepository


class TenantRepository(CRUDRepository[Tenant]):
    """租户仓储。"""

    def __init__(self) -> None:
        super().__init__(Tenant)

    def get_by_slug(self, db: Session, *, slug: str) -> Optional[Tenant]:
        stmt: Select[tuple[Tenant]] = select(Tenant).where(Tenant.slug == slug)
        return db.execute(stmt).scalars().first()

    def get_by_name(self, db: Session, *, name: str) -> Optional[Tenant]:
        stmt: Select[tuple[Tenant]] = select(Tenant).where(Tenant.name == name)
        return db.execute(stmt).scalars().first()

    def count_members(self, db: Session, *, tenant_id: str) -> int:
        from app.models.tenant_member import TenantMember

        stmt = select(func.count()).select_from(TenantMember).where(TenantMember.tenant_id == tenant_id)
        return db.execute(stmt).scalar_one()


class TenantApplicationRepository(CRUDRepository[TenantApplication]):
    """租户入驻申请仓储。"""

    def __init__(self) -> None:
        super().__init__(TenantApplication)
    
    # 查询待审核的同公司申请
    def find_pending_by_email(
        self,
        db: Session,
        *,
        contact_email: str,
    ) -> Optional[TenantApplication]:
        stmt = select(TenantApplication).where(
            TenantApplication.contact_email == contact_email,
            TenantApplication.status == ApplicationStatus.PENDING,
        )
        return db.execute(stmt).scalars().first()

    # 查询待审核的同公司和邮箱的申请
    def find_pending_by_company_and_email(
        self,
        db: Session,
        *,
        company_name: str,
        contact_email: str,
    ) -> Optional[TenantApplication]:
        stmt = (
            select(TenantApplication)
            .where(
                TenantApplication.company_name == company_name,
                TenantApplication.contact_email == contact_email,
                TenantApplication.status == ApplicationStatus.PENDING,
            )
        )
        return db.execute(stmt).scalars().first()

    # 查询指定状态的申请
    def list_by_status(
        self,
        db: Session,
        *,
        status: Optional[ApplicationStatus] = None,
    ) -> list[TenantApplication]:
        stmt: Select[tuple[TenantApplication]] = select(TenantApplication)
        if status:
            stmt = stmt.where(TenantApplication.status == status)
        return db.execute(stmt).scalars().all()
