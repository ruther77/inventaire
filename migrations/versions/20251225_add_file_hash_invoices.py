"""Add file_hash column to processed_invoices for duplicate prevention (P1)."""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "20251225_add_file_hash"
down_revision: Union[str, Sequence[str], None] = "b62f12b01988"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # Check if column already exists
    columns = {col["name"] for col in inspector.get_columns("processed_invoices")}

    if "file_hash" not in columns:
        op.add_column(
            "processed_invoices",
            sa.Column("file_hash", sa.String(64), nullable=True)
        )

    # Check if index already exists
    indexes = {idx["name"] for idx in inspector.get_indexes("processed_invoices")}

    if "idx_processed_invoices_hash" not in indexes:
        op.create_index(
            "idx_processed_invoices_hash",
            "processed_invoices",
            ["file_hash"],
            unique=True,
            postgresql_where=sa.text("file_hash IS NOT NULL")
        )


def downgrade() -> None:
    op.drop_index("idx_processed_invoices_hash", table_name="processed_invoices")
    op.drop_column("processed_invoices", "file_hash")
