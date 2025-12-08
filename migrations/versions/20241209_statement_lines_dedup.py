"""Ajout d'index unique pour la déduplication cross-statement des lignes bancaires."""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision: str = "20241209_statement_lines_dedup"
down_revision: Union[str, Sequence[str], None] = "20241208_finance_ui_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # Ajout d'une colonne account_id dénormalisée pour faciliter la déduplication
    cols = {col["name"] for col in inspector.get_columns("finance_bank_statement_lines")}
    if "account_id" not in cols:
        op.add_column(
            "finance_bank_statement_lines",
            sa.Column("account_id", sa.BigInteger(), nullable=True),
        )
        # Remplir account_id depuis la jointure avec finance_bank_statements
        bind.execute(
            text(
                """
                UPDATE finance_bank_statement_lines l
                SET account_id = s.account_id
                FROM finance_bank_statements s
                WHERE l.statement_id = s.id AND l.account_id IS NULL
                """
            )
        )
        # Ajouter une FK
        op.create_foreign_key(
            "fk_statement_lines_account",
            "finance_bank_statement_lines",
            "finance_accounts",
            ["account_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # Index unique partiel: un seul checksum par compte (si checksum non null)
    existing_indexes = {idx["name"] for idx in inspector.get_indexes("finance_bank_statement_lines")}
    if "uq_statement_lines_account_checksum" not in existing_indexes:
        # Supprimer les doublons existants avant de créer la contrainte
        bind.execute(
            text(
                """
                DELETE FROM finance_bank_statement_lines
                WHERE id NOT IN (
                    SELECT MIN(id) FROM finance_bank_statement_lines
                    WHERE checksum IS NOT NULL
                    GROUP BY account_id, checksum
                )
                AND checksum IS NOT NULL
                """
            )
        )
        op.create_index(
            "uq_statement_lines_account_checksum",
            "finance_bank_statement_lines",
            ["account_id", "checksum"],
            unique=True,
            postgresql_where=sa.text("checksum IS NOT NULL"),
        )


def downgrade() -> None:
    op.drop_index("uq_statement_lines_account_checksum", table_name="finance_bank_statement_lines")
    op.drop_constraint("fk_statement_lines_account", "finance_bank_statement_lines", type_="foreignkey")
    op.drop_column("finance_bank_statement_lines", "account_id")
