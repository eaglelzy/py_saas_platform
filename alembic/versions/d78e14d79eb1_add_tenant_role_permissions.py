"""Add tenant role permissions

Revision ID: d78e14d79eb1
Revises: 6ca591fa14fc
Create Date: 2025-10-25 20:58:58.858633

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd78e14d79eb1'
down_revision: Union[str, None] = '6ca591fa14fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tenant_role_permissions',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('tenant_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.Column('permission', sa.String(length=120), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index('ix_role_permission_tenant_role', 'tenant_role_permissions', ['tenant_id', 'role'])


def downgrade() -> None:
    op.drop_index('ix_role_permission_tenant_role', table_name='tenant_role_permissions')
    op.drop_table('tenant_role_permissions')
