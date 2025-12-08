"""Indexes perfs filtres finance (transactions, relevés, texte)."""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20241207_finance_perf_indexes"
down_revision: Union[str, Sequence[str], None] = "20241203_finance_treasury"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extensions nécessaires pour trigram.
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_finance_transactions_entity_account_date "
        "ON finance_transactions (entity_id, account_id, date_operation)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_finance_transaction_lines_category "
        "ON finance_transaction_lines (category_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_finance_bank_statements_account_period "
        "ON finance_bank_statements (account_id, period_start, period_end)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_finance_bank_statement_lines_stmt_date "
        "ON finance_bank_statement_lines (statement_id, date_operation)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_finance_transactions_note_trgm "
        "ON finance_transactions USING gin (note gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_finance_bank_stmt_lines_libelle_trgm "
        "ON finance_bank_statement_lines USING gin (libelle_banque gin_trgm_ops)"
    )


def downgrade() -> None:
    op.drop_index("ix_finance_bank_stmt_lines_libelle_trgm", table_name="finance_bank_statement_lines")
    op.drop_index("ix_finance_transactions_note_trgm", table_name="finance_transactions")
    op.drop_index("ix_finance_bank_statement_lines_stmt_date", table_name="finance_bank_statement_lines")
    op.drop_index("ix_finance_bank_statements_account_period", table_name="finance_bank_statements")
    op.drop_index("ix_finance_transaction_lines_category", table_name="finance_transaction_lines")
    op.drop_index("ix_finance_transactions_entity_account_date", table_name="finance_transactions")
