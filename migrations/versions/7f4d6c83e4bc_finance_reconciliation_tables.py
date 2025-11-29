"""finance reconciliation tables

Revision ID: 7f4d6c83e4bc
Revises: 09f118fbd720
Create Date: 2025-11-14 18:05:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "7f4d6c83e4bc"
down_revision: Union[str, Sequence[str], None] = "09f118fbd720"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "finance_invoice_documents",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("supplier_name", sa.Text(), nullable=False),
        sa.Column("invoice_reference", sa.Text(), nullable=False),
        sa.Column("invoice_number", sa.Text(), nullable=True),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("total_excl_tax", sa.Numeric(18, 2), nullable=True),
        sa.Column("total_incl_tax", sa.Numeric(18, 2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "invoice_reference", name="uq_finance_invoice_documents_reference"),
    )

    op.add_column(
        "fact_invoices",
        sa.Column("document_id", sa.BigInteger(), nullable=True),
    )
    op.create_foreign_key(
        "fk_fact_invoices_document",
        "fact_invoices",
        "finance_invoice_documents",
        ["document_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_fact_invoices_document_id", "fact_invoices", ["document_id"])

    op.create_table(
        "finance_reconciliation_runs",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="running"),
        sa.Column("params", postgresql.JSONB(), nullable=True),
        sa.Column("stats", postgresql.JSONB(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "finance_bank_invoice_matches",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.BigInteger(), sa.ForeignKey("finance_reconciliation_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("bank_statement_id", sa.Integer(), sa.ForeignKey("restaurant_bank_statements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", sa.BigInteger(), sa.ForeignKey("finance_invoice_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("match_type", sa.Text(), nullable=False, server_default="heuristic"),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("score", sa.Numeric(6, 4), nullable=False, server_default="0"),
        sa.Column("bank_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("invoice_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("amount_diff", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("days_diff", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("bank_statement_id", "document_id", name="uq_finance_match_pair"),
    )
    op.create_index(
        "ix_finance_matches_tenant_status",
        "finance_bank_invoice_matches",
        ["tenant_id", "status", "score"],
    )

    # Backfill finance_invoice_documents with existing fact_invoices data
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO finance_invoice_documents (
                tenant_id,
                supplier_id,
                supplier_name,
                invoice_reference,
                invoice_number,
                invoice_date,
                total_excl_tax,
                total_incl_tax,
                currency,
                metadata
            )
            SELECT
                fi.tenant_id,
                fi.supplier_id,
                ds.name AS supplier_name,
                COALESCE(NULLIF(fi.invoice_number, ''), CONCAT('import-', fi.tenant_id, '-', fi.supplier_id, '-', dd.date_value)) AS invoice_reference,
                fi.invoice_number,
                dd.date_value,
                SUM(COALESCE(fi.quantity, 0) * COALESCE(fi.unit_cost_excl_tax, 0)) AS total_excl_tax,
                SUM(COALESCE(fi.quantity, 0) * COALESCE(fi.unit_cost_excl_tax, 0) * (1 + COALESCE(fi.vat_rate, 0) / 100)) AS total_incl_tax,
                MAX(fi.currency) AS currency,
                jsonb_build_object('line_count', COUNT(*))
            FROM fact_invoices fi
            JOIN dim_supplier ds ON ds.id = fi.supplier_id
            JOIN dim_date dd ON dd.id = fi.date_id
            GROUP BY
                fi.tenant_id,
                fi.supplier_id,
                ds.name,
                COALESCE(NULLIF(fi.invoice_number, ''), CONCAT('import-', fi.tenant_id, '-', fi.supplier_id, '-', dd.date_value)),
                fi.invoice_number,
                dd.date_value
            ON CONFLICT (tenant_id, invoice_reference) DO NOTHING
            """
        )
    )

    conn.execute(
        sa.text(
            """
            UPDATE fact_invoices fi
            SET document_id = doc.id
            FROM finance_invoice_documents doc, dim_date dd
            WHERE doc.tenant_id = fi.tenant_id
              AND doc.supplier_id = fi.supplier_id
              AND dd.id = fi.date_id
              AND doc.invoice_reference = COALESCE(
                    NULLIF(fi.invoice_number, ''),
                    CONCAT('import-', fi.tenant_id, '-', fi.supplier_id, '-', dd.date_value)
                )
              AND doc.invoice_date = dd.date_value
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_finance_matches_tenant_status", table_name="finance_bank_invoice_matches")
    op.drop_table("finance_bank_invoice_matches")
    op.drop_table("finance_reconciliation_runs")
    op.drop_index("ix_fact_invoices_document_id", table_name="fact_invoices")
    op.drop_constraint("fk_fact_invoices_document", "fact_invoices", type_="foreignkey")
    op.drop_column("fact_invoices", "document_id")
    op.drop_table("finance_invoice_documents")
