"""inventory cost layers

Revision ID: b4f8fb1c1e5d
Revises: 4f6f4b09928b
Create Date: 2025-11-14 20:05:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b4f8fb1c1e5d"
down_revision: Union[str, Sequence[str], None] = "4f6f4b09928b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "produits",
        sa.Column(
            "average_cost",
            sa.Numeric(12, 4),
            nullable=False,
            server_default="0",
        ),
    )

    op.create_table(
        "inventory_cost_layers",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("produits.id", ondelete="CASCADE"), nullable=False),
        sa.Column("movement_id", sa.Integer(), sa.ForeignKey("mouvements_stock.id", ondelete="SET NULL"), nullable=True),
        sa.Column("quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("quantity_remaining", sa.Numeric(14, 3), nullable=False),
        sa.Column("unit_cost", sa.Numeric(12, 4), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("source", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("is_depleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_inventory_cost_layers_product",
        "inventory_cost_layers",
        ["tenant_id", "product_id", "is_depleted"],
    )


def downgrade() -> None:
    op.drop_index("ix_inventory_cost_layers_product", table_name="inventory_cost_layers")
    op.drop_table("inventory_cost_layers")
    op.drop_column("produits", "average_cost")
