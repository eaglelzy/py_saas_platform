"""Enable row level security policies for tenant scoped tables.

Revision ID: 13a3c9ad8b69
Revises: d78e14d79eb1
Create Date: 2025-01-19 10:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Tuple

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "13a3c9ad8b69"
down_revision: str | None = "d78e14d79eb1"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


TENANT_SCOPED_TABLES: Tuple[Tuple[str, str], ...] = (
    ("tenant_members", "tenant_id"),
    ("member_invitations", "tenant_id"),
    ("tenant_role_permissions", "tenant_id"),
    ("tenant_subscriptions", "tenant_id"),
    ("subscription_orders", "tenant_id"),
)


def _policy_name(table: str, action: str) -> str:
    return f"{table}_{action}_tenant_policy"


def upgrade() -> None:
    for table, column in TENANT_SCOPED_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")

        select_policy = f"""
        CREATE POLICY {_policy_name(table, 'select')}
        ON {table}
        FOR SELECT
        USING (
            {column} = current_setting('app.current_tenant', true)::uuid
        );
        """

        mutate_policy = f"""
        CREATE POLICY {_policy_name(table, 'modify')}
        ON {table}
        FOR ALL
        USING (
            {column} = current_setting('app.current_tenant', true)::uuid
        )
        WITH CHECK (
            {column} = current_setting('app.current_tenant', true)::uuid
        );
        """

        op.execute(select_policy)
        op.execute(mutate_policy)


def downgrade() -> None:
    for table, _ in reversed(TENANT_SCOPED_TABLES):
        op.execute(f"DROP POLICY IF EXISTS {_policy_name(table, 'modify')} ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {_policy_name(table, 'select')} ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

