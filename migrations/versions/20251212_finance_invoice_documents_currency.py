"""Ajout colonne currency sur finance_invoice_documents."""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20251212_finance_invoice_documents_currency"
down_revision: Union[str, Sequence[str], None] = "20251212_finance_invoice_documents_cols"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("finance_invoice_documents") as batch:
        batch.add_column(sa.Column("currency", sa.Text(), nullable=False, server_default="EUR"))


def downgrade() -> None:
    with op.batch_alter_table("finance_invoice_documents") as batch:
        batch.drop_column("currency")
