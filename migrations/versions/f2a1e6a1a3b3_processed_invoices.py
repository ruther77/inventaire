"""Create processed_invoices table to track imported documents."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "f2a1e6a1a3b3"
down_revision = "e32e12bd5139"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "processed_invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.Text(), nullable=False),
        sa.Column("supplier", sa.Text(), nullable=True),
        sa.Column("facture_date", sa.Text(), nullable=True),
        sa.Column("line_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "invoice_id", name="uq_processed_invoice"),
    )
    op.create_index("idx_processed_invoices_tenant", "processed_invoices", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("idx_processed_invoices_tenant", table_name="processed_invoices")
    op.drop_table("processed_invoices")
