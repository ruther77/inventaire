"""restaurant plat costs and alerts

Revision ID: d72cb3da9a7c
Revises: c8329b8cc5e7
Create Date: 2025-11-14 20:46:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d72cb3da9a7c"
down_revision: Union[str, Sequence[str], None] = "c8329b8cc5e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "restaurant_plat_costs",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column(
            "plat_id",
            sa.Integer(),
            sa.ForeignKey("restaurant_plats.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("cout_matiere", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("prix_vente_ttc", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("marge_brute", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("marge_pct", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "plat_id", name="uq_restaurant_plat_cost"),
    )
    op.create_index(
        "ix_restaurant_plat_costs_tenant",
        "restaurant_plat_costs",
        ["tenant_id", "marge_pct"],
    )

    op.create_table(
        "restaurant_alerts",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column(
            "plat_id",
            sa.Integer(),
            sa.ForeignKey("restaurant_plats.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("alert_type", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False, server_default="warning"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("current_value", sa.Numeric(12, 4), nullable=True),
        sa.Column("threshold", sa.Numeric(12, 4), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_restaurant_alerts_tenant",
        "restaurant_alerts",
        ["tenant_id", "alert_type", "severity"],
    )


def downgrade() -> None:
    op.drop_index("ix_restaurant_alerts_tenant", table_name="restaurant_alerts")
    op.drop_table("restaurant_alerts")
    op.drop_index("ix_restaurant_plat_costs_tenant", table_name="restaurant_plat_costs")
    op.drop_table("restaurant_plat_costs")
