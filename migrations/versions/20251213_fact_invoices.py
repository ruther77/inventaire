"""Création de fact_invoices pour consolidation factures."""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20251213_fact_invoices"
down_revision: Union[str, Sequence[str], None] = "20251212_finance_invoice_documents_metadata"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fact_invoices",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("date_id", sa.BigInteger(), nullable=False),
        sa.Column("supplier_id", sa.BigInteger(), nullable=False),
        sa.Column("document_id", sa.BigInteger(), nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("category_id", sa.BigInteger(), nullable=True),
        sa.Column("invoice_number", sa.Text(), nullable=True),
        sa.Column("sku", sa.Text(), nullable=True),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("unit_cost_excl_tax", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("vat_rate", sa.Numeric(5, 2), nullable=True),
        sa.Column("currency", sa.Text(), nullable=False, server_default="EUR"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_fact_invoices_tenant_date_supplier",
        "fact_invoices",
        ["tenant_id", "date_id", "supplier_id"],
    )
    op.create_index(
        "ix_fact_invoices_product",
        "fact_invoices",
        ["product_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_fact_invoices_product", table_name="fact_invoices")
    op.drop_index("ix_fact_invoices_tenant_date_supplier", table_name="fact_invoices")
    op.drop_table("fact_invoices")
