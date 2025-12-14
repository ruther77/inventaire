"""Ajout colonne metadata sur finance_invoice_documents."""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20251212_finance_invoice_documents_metadata"
down_revision: Union[str, Sequence[str], None] = "20251212_finance_invoice_documents_currency"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("finance_invoice_documents") as batch:
        batch.add_column(sa.Column("metadata", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("finance_invoice_documents") as batch:
        batch.drop_column("metadata")
