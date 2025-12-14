"""Point finance_bank_invoice_matches.bank_statement_id vers finance_bank_statement_lines."""

from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "20251213_finance_matches_fk_lines"
down_revision = "20251213_finance_matches_unique_idx"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        -- purge des anciens matches pour éviter les FK invalides
        DELETE FROM finance_bank_invoice_matches;
        ALTER TABLE finance_bank_invoice_matches
        DROP CONSTRAINT IF EXISTS fk_finance_bank_invoice_matches_stmt;

        ALTER TABLE finance_bank_invoice_matches
        ADD CONSTRAINT fk_finance_bank_invoice_matches_stmt_lines
            FOREIGN KEY (bank_statement_id)
            REFERENCES finance_bank_statement_lines(id)
            ON DELETE CASCADE;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE finance_bank_invoice_matches
        DROP CONSTRAINT IF EXISTS fk_finance_bank_invoice_matches_stmt_lines;
        -- NOTE: on ne rétablit pas l'ancien FK vers restaurant_bank_statements par sécurité.
        """
    )
