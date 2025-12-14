"""Add unique index on bank_statement_id/document_id for matches."""

from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "20251213_finance_matches_unique_idx"
down_revision = "20251213_finance_matches_run_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_finance_bank_invoice_matches_stmt_doc
            ON finance_bank_invoice_matches (bank_statement_id, document_id);
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP INDEX IF EXISTS uq_finance_bank_invoice_matches_stmt_doc"
    )
