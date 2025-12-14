"""Create finance_reconciliation_runs table for bank<->invoice matching."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251213_finance_reconciliation_runs"
down_revision = "20251213_fact_invoices"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS finance_reconciliation_runs (
            id BIGSERIAL PRIMARY KEY,
            tenant_id BIGINT NOT NULL,
            status TEXT NOT NULL DEFAULT 'running',
            params JSONB,
            stats JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            completed_at TIMESTAMPTZ
        );
        CREATE INDEX IF NOT EXISTS ix_finance_reconciliation_runs_tenant_status
            ON finance_reconciliation_runs (tenant_id, status);
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS finance_reconciliation_runs")
