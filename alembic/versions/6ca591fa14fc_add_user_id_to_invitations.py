"""Add user_id to invitations

Revision ID: 6ca591fa14fc
Revises: ef8b502a8a88
Create Date: 2025-10-25 20:34:23.200590

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6ca591fa14fc'
down_revision: Union[str, None] = 'ef8b502a8a88'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'member_invitations',
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        'fk_member_invitation_user',
        'member_invitations',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    op.drop_constraint('fk_member_invitation_user', 'member_invitations', type_='foreignkey')
    op.drop_column('member_invitations', 'user_id')
