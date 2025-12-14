"""Ajout colonnes supplier/updated_at sur finance_invoice_documents."""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20251212_finance_invoice_documents_cols"
down_revision: Union[str, Sequence[str], None] = "20251212_dim_supplier_category_product"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    existing_cols = {
        row[0]
        for row in conn.execute(
            sa.text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'finance_invoice_documents'"
            )
        )
    }
    with op.batch_alter_table("finance_invoice_documents") as batch:
        if "supplier_id" not in existing_cols:
            batch.add_column(sa.Column("supplier_id", sa.BigInteger(), nullable=True))
        if "supplier_name" not in existing_cols:
            batch.add_column(sa.Column("supplier_name", sa.Text(), nullable=True))
        if "updated_at" not in existing_cols:
            batch.add_column(
                sa.Column(
                    "updated_at",
                    sa.DateTime(timezone=True),
                    server_default=sa.func.now(),
                    nullable=True,
                )
            )
        batch.create_index(
            "ix_finance_invoice_documents_tenant_reference",
            ["tenant_id", "invoice_reference"],
            unique=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("finance_invoice_documents") as batch:
        batch.drop_index("ix_finance_invoice_documents_tenant_reference")
        batch.drop_column("updated_at")
        batch.drop_column("supplier_id")
