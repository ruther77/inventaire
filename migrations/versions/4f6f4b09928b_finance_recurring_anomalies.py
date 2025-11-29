"""finance recurring expenses and anomalies tables

Revision ID: 4f6f4b09928b
Revises: 7f4d6c83e4bc
Create Date: 2025-11-14 18:45:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "4f6f4b09928b"
down_revision: Union[str, Sequence[str], None] = "7f4d6c83e4bc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "finance_recurring_expenses",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("normalized_label", sa.Text(), nullable=False),
        sa.Column("sample_label", sa.Text(), nullable=False),
        sa.Column("account", sa.Text(), nullable=True),
        sa.Column("category", sa.Text(), nullable=True),
        sa.Column("periodicity", sa.Text(), nullable=False, server_default="unknown"),
        sa.Column("occurrences", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("std_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("first_date", sa.Date(), nullable=True),
        sa.Column("last_date", sa.Date(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "tenant_id",
            "normalized_label",
            "account",
            name="uq_finance_recurring_label_account",
        ),
    )
    op.create_index(
        "ix_finance_recurring_tenant_periodicity",
        "finance_recurring_expenses",
        ["tenant_id", "periodicity"],
    )

    op.create_table(
        "finance_anomaly_flags",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column(
            "bank_statement_id",
            sa.Integer(),
            sa.ForeignKey("restaurant_bank_statements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rule", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False, server_default="warning"),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("score", sa.Numeric(6, 4), nullable=True),
        sa.Column("amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("expected_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "bank_statement_id", "rule", name="uq_finance_anomaly_per_rule"),
    )
    op.create_index(
        "ix_finance_anomalies_tenant_severity",
        "finance_anomaly_flags",
        ["tenant_id", "severity"],
    )


def downgrade() -> None:
    op.drop_index("ix_finance_anomalies_tenant_severity", table_name="finance_anomaly_flags")
    op.drop_table("finance_anomaly_flags")
    op.drop_index("ix_finance_recurring_tenant_periodicity", table_name="finance_recurring_expenses")
    op.drop_table("finance_recurring_expenses")
