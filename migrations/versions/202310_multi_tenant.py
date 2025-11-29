"""Add tenant_id columns to support multi-tenant (epicerie/restaurant)."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "202310_multi_tenant"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.execute(
        """
        INSERT INTO tenants (id, name, code)
        VALUES (1, 'Epicerie HQ', 'epicerie'), (2, 'Restaurant HQ', 'restaurant')
        ON CONFLICT (id) DO NOTHING
        """
    )

    for table in ("produits", "produits_barcodes", "mouvements_stock", "audit_actions", "audit_resolution_log"):
        op.add_column(table, sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"))

    op.add_column(
        "produits_price_history",
        sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    for table in ("produits_price_history", "audit_resolution_log", "audit_actions", "mouvements_stock", "produits_barcodes", "produits"):
        op.drop_column(table, "tenant_id")
    op.drop_table("tenants")
