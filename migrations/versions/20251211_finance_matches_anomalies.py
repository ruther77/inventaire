"""Ajout tables de rapprochement et colonnes manquantes pour finance."""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20251211_finance_fix"
down_revision: Union[str, Sequence[str], None] = "20241209_statement_lines_dedup"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Harmonisation finance_transactions (alias montant/date_transaction pour compatibilité requêtes)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'finance_transactions' AND column_name = 'montant'
            ) THEN
                ALTER TABLE finance_transactions ADD COLUMN montant NUMERIC(18,2);
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'finance_transactions' AND column_name = 'date_transaction'
            ) THEN
                ALTER TABLE finance_transactions ADD COLUMN date_transaction DATE;
            END IF;
        END
        $$;
        """
    )

    # processed_invoices: total_ttc attendu par le front
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'processed_invoices' AND column_name = 'total_ttc'
            ) THEN
                ALTER TABLE processed_invoices ADD COLUMN total_ttc NUMERIC(18,2);
            END IF;

        END
        $$;
        """
    )

    # Table finance_invoice_documents (stub si absente, utilisée par les FK)
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS finance_invoice_documents (
            id BIGSERIAL PRIMARY KEY,
            tenant_id BIGINT,
            invoice_reference TEXT,
            invoice_number TEXT,
            invoice_date DATE,
            total_incl_tax NUMERIC(18,2),
            total_excl_tax NUMERIC(18,2),
            supplier_name TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )

    # Table des matches banque <-> factures (utilisée par le rapprochement IA)
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS finance_bank_invoice_matches (
            id BIGSERIAL PRIMARY KEY,
            tenant_id BIGINT NOT NULL,
            bank_statement_id BIGINT NOT NULL,
            document_id BIGINT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            match_type TEXT,
            score NUMERIC(5,2),
            bank_amount NUMERIC(18,2),
            invoice_amount NUMERIC(18,2),
            amount_diff NUMERIC(18,2),
            days_diff INTEGER,
            explanation TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT fk_finance_bank_invoice_matches_stmt FOREIGN KEY (bank_statement_id)
                REFERENCES restaurant_bank_statements (id) ON DELETE CASCADE,
            CONSTRAINT fk_finance_bank_invoice_matches_doc FOREIGN KEY (document_id)
                REFERENCES finance_invoice_documents (id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS ix_finance_bank_invoice_matches_tenant_status
            ON finance_bank_invoice_matches (tenant_id, status);
        """
    )

    # Table des anomalies de rapprochement
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS finance_anomaly_flags (
            id BIGSERIAL PRIMARY KEY,
            tenant_id BIGINT NOT NULL,
            bank_statement_id BIGINT,
            rule TEXT,
            severity TEXT,
            message TEXT,
            score NUMERIC(5,2),
            amount NUMERIC(18,2),
            expected_amount NUMERIC(18,2),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT fk_finance_anomaly_flags_stmt FOREIGN KEY (bank_statement_id)
                REFERENCES restaurant_bank_statements (id) ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS ix_finance_anomaly_flags_tenant_severity
            ON finance_anomaly_flags (tenant_id, severity);
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS finance_anomaly_flags")
    op.execute("DROP TABLE IF EXISTS finance_bank_invoice_matches")
    op.execute(
        "ALTER TABLE processed_invoices DROP COLUMN IF EXISTS total_ttc"
    )
    op.execute(
        "ALTER TABLE finance_transactions DROP COLUMN IF EXISTS date_transaction"
    )
    op.execute(
        "ALTER TABLE finance_transactions DROP COLUMN IF EXISTS montant"
    )
