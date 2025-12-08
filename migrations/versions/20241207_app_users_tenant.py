"""Add tenant_id to app_users for multi-tenant user access control.

Each user can be associated with one or more tenants.
For now, we add a simple tenant_id column with a default of 1 (epicerie).
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20241207_app_users_tenant"
down_revision = "20241208_fin_rules"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add tenant_id column to app_users
    op.add_column(
        "app_users",
        sa.Column(
            "tenant_id",
            sa.Integer(),
            nullable=False,
            server_default="1"
        )
    )

    # Create foreign key to tenants table
    op.create_foreign_key(
        "fk_app_users_tenant",
        "app_users",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE"
    )

    # Create index for faster tenant filtering
    op.create_index(
        "idx_app_users_tenant",
        "app_users",
        ["tenant_id"]
    )

    # Add is_active column for soft delete capability
    op.add_column(
        "app_users",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.sql.expression.true()
        )
    )

    # Add last_login timestamp
    op.add_column(
        "app_users",
        sa.Column(
            "last_login",
            sa.DateTime(timezone=True),
            nullable=True
        )
    )


def downgrade() -> None:
    op.drop_column("app_users", "last_login")
    op.drop_column("app_users", "is_active")
    op.drop_index("idx_app_users_tenant", table_name="app_users")
    op.drop_constraint("fk_app_users_tenant", "app_users", type_="foreignkey")
    op.drop_column("app_users", "tenant_id")
