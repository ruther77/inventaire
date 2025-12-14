"""Add run_id to finance_bank_invoice_matches."""

from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "20251213_finance_matches_run_id"
down_revision = "20251213_finance_reconciliation_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE finance_bank_invoice_matches
        ADD COLUMN IF NOT EXISTS run_id BIGINT;
        CREATE INDEX IF NOT EXISTS ix_finance_bank_invoice_matches_run
            ON finance_bank_invoice_matches (run_id);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS ix_finance_bank_invoice_matches_run;
        ALTER TABLE finance_bank_invoice_matches DROP COLUMN IF EXISTS run_id;
        """
    )
