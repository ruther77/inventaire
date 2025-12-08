"""Table finance_rules et historisation imports."""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20241208_fin_rules"
down_revision: Union[str, Sequence[str], None] = "20241207_finance_perf_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "finance_rules",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("entity_id", sa.BigInteger(), nullable=False),
        sa.Column("category_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("keywords", sa.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("apply_to_autre_only", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_finance_rules_entity", "finance_rules", ["entity_id"], unique=False)
    op.create_index("ix_finance_rules_active", "finance_rules", ["is_active"], unique=False)

    op.create_table(
        "finance_imports",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("file_name", sa.Text(), nullable=True),
        sa.Column("source", sa.Text(), nullable=True),
        sa.Column("inserted", sa.Integer(), nullable=True),
        sa.Column("total", sa.Integer(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="DONE"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_finance_imports_account", "finance_imports", ["account_id"], unique=False)
    op.create_index("ix_finance_imports_status", "finance_imports", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_finance_imports_status", table_name="finance_imports")
    op.drop_index("ix_finance_imports_account", table_name="finance_imports")
    op.drop_table("finance_imports")
    op.drop_index("ix_finance_rules_active", table_name="finance_rules")
    op.drop_index("ix_finance_rules_entity", table_name="finance_rules")
    op.drop_table("finance_rules")
