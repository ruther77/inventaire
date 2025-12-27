"""Add restaurant_sales table for SumUp sales imports."""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "20251226_add_restaurant_sales"
down_revision: Union[str, Sequence[str], None] = "20251225_add_soft_delete"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    if "restaurant_sales" not in tables:
        op.create_table(
            "restaurant_sales",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("tenant_id", sa.Integer(), nullable=False),
            sa.Column(
                "plat_id",
                sa.Integer(),
                sa.ForeignKey("restaurant_plats.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("quantity", sa.Numeric(12, 4), nullable=False),
            sa.Column("sold_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("source", sa.Text(), nullable=True),
            sa.Column("source_ref", sa.Text(), nullable=True),
            sa.Column("row_hash", sa.String(40), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )
    else:
        columns = {col["name"] for col in inspector.get_columns("restaurant_sales")}
        if "source_ref" not in columns:
            op.add_column("restaurant_sales", sa.Column("source_ref", sa.Text(), nullable=True))
        if "row_hash" not in columns:
            op.add_column("restaurant_sales", sa.Column("row_hash", sa.String(40), nullable=True))
        if "created_at" not in columns:
            op.add_column(
                "restaurant_sales",
                sa.Column(
                    "created_at",
                    sa.DateTime(timezone=True),
                    server_default=sa.text("now()"),
                    nullable=True,
                ),
            )

    indexes = {idx["name"] for idx in inspector.get_indexes("restaurant_sales")}
    if "uq_restaurant_sales_row_hash" not in indexes:
        op.create_index(
            "uq_restaurant_sales_row_hash",
            "restaurant_sales",
            ["tenant_id", "row_hash"],
            unique=True,
            postgresql_where=sa.text("row_hash IS NOT NULL"),
        )
    if "idx_restaurant_sales_tenant_sold_at" not in indexes:
        op.create_index(
            "idx_restaurant_sales_tenant_sold_at",
            "restaurant_sales",
            ["tenant_id", "sold_at"],
        )
    if "idx_restaurant_sales_plat_sold_at" not in indexes:
        op.create_index(
            "idx_restaurant_sales_plat_sold_at",
            "restaurant_sales",
            ["plat_id", "sold_at"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "restaurant_sales" not in inspector.get_table_names():
        return

    indexes = {idx["name"] for idx in inspector.get_indexes("restaurant_sales")}
    if "idx_restaurant_sales_plat_sold_at" in indexes:
        op.drop_index("idx_restaurant_sales_plat_sold_at", table_name="restaurant_sales")
    if "idx_restaurant_sales_tenant_sold_at" in indexes:
        op.drop_index("idx_restaurant_sales_tenant_sold_at", table_name="restaurant_sales")
    if "uq_restaurant_sales_row_hash" in indexes:
        op.drop_index("uq_restaurant_sales_row_hash", table_name="restaurant_sales")

    op.drop_table("restaurant_sales")
