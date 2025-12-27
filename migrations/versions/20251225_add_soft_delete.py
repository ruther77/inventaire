"""Add soft delete columns to critical tables for audit trail and data recovery."""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "20251225_add_soft_delete"
down_revision: Union[str, Sequence[str], None] = "20251225_add_scoring_profiles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add soft delete columns to critical tables."""
    bind = op.get_bind()
    inspector = inspect(bind)

    # List of critical tables that need soft delete
    tables = ["produits", "finance_transactions", "processed_invoices", "restaurant_plats"]

    for table_name in tables:
        # Check if table exists
        if table_name not in inspector.get_table_names():
            continue

        # Get existing columns for this table
        columns = {col["name"] for col in inspector.get_columns(table_name)}

        # Add deleted_at column if it doesn't exist
        if "deleted_at" not in columns:
            op.add_column(
                table_name,
                sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True)
            )

        # Add deleted_by column if it doesn't exist
        if "deleted_by" not in columns:
            op.add_column(
                table_name,
                sa.Column("deleted_by", sa.String(100), nullable=True)
            )

        # Get existing indexes for this table
        indexes = {idx["name"] for idx in inspector.get_indexes(table_name)}

        # Create partial index for non-deleted records
        index_name = f"idx_{table_name}_not_deleted"
        if index_name not in indexes:
            op.create_index(
                index_name,
                table_name,
                ["id"],
                unique=False,
                postgresql_where=sa.text("deleted_at IS NULL")
            )


def downgrade() -> None:
    """Remove soft delete columns from critical tables."""
    bind = op.get_bind()
    inspector = inspect(bind)

    tables = ["produits", "finance_transactions", "processed_invoices", "restaurant_plats"]

    for table_name in tables:
        # Check if table exists
        if table_name not in inspector.get_table_names():
            continue

        # Drop index if it exists
        index_name = f"idx_{table_name}_not_deleted"
        indexes = {idx["name"] for idx in inspector.get_indexes(table_name)}
        if index_name in indexes:
            op.drop_index(index_name, table_name=table_name)

        # Drop columns if they exist
        columns = {col["name"] for col in inspector.get_columns(table_name)}
        if "deleted_by" in columns:
            op.drop_column(table_name, "deleted_by")
        if "deleted_at" in columns:
            op.drop_column(table_name, "deleted_at")
