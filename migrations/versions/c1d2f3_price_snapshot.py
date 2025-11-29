"""Ajout table capital_snapshot et vue latest_price_history."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "c1d2f3_price_snapshot"
down_revision = "ba1f96ef4dfd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "capital_snapshot" not in inspector.get_table_names():
        op.create_table(
            "capital_snapshot",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("tenant_id", sa.Integer(), nullable=False),
            sa.Column("snapshot_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("stock_value", sa.Numeric(14, 2), nullable=False, server_default="0"),
            sa.Column("bank_balance", sa.Numeric(14, 2), nullable=False, server_default="0"),
            sa.Column("cash_balance", sa.Numeric(14, 2), nullable=False, server_default="0"),
            sa.Column("total_assets", sa.Numeric(14, 2), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    existing_indexes = {index["name"] for index in inspector.get_indexes("capital_snapshot")}
    if "idx_capital_snapshot_tenant_date" not in existing_indexes:
        op.create_index("idx_capital_snapshot_tenant_date", "capital_snapshot", ["tenant_id", "snapshot_date"])

    op.execute(
        """
        CREATE OR REPLACE VIEW latest_price_history AS
        SELECT code, tenant_id, fournisseur, prix_achat, quantite, facture_date, source_context, created_at
        FROM (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY tenant_id, code
                       ORDER BY facture_date DESC NULLS LAST, created_at DESC
                   ) AS row_num
            FROM produits_price_history
        ) ranked
        WHERE row_num = 1
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS latest_price_history")
    op.drop_index("idx_capital_snapshot_tenant_date", table_name="capital_snapshot")
    op.drop_table("capital_snapshot")
