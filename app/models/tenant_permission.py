"""租户角色权限模型。"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.tenant_member import TenantMemberRole


class TenantRolePermission(Base):
    """租户角色与权限的映射。"""

    __tablename__ = "tenant_role_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(32), nullable=False)
    permission = Column(String(120), nullable=False)

    tenant = relationship("Tenant", backref="role_permissions")

