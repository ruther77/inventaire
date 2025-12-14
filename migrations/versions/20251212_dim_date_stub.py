"""Ajout table dim_date pour la consolidation factures."""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20251212_dim_date_stub"
down_revision: Union[str, Sequence[str], None] = "20251212_dim_tenant_stub"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'dim_date' AND column_name = 'id'
            ) THEN
                ALTER TABLE dim_date ADD COLUMN id BIGSERIAL;
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_name = 'dim_date' AND constraint_type = 'PRIMARY KEY'
            ) THEN
                ALTER TABLE dim_date DROP CONSTRAINT dim_date_pkey;
            END IF;
            ALTER TABLE dim_date ADD PRIMARY KEY (id);
            CREATE UNIQUE INDEX IF NOT EXISTS uq_dim_date_value ON dim_date(date_value);
        END
        $$;
        """
    )


def downgrade() -> None:
    op.drop_table("dim_date")
