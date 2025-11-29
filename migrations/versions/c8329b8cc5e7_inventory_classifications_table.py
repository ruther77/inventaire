"""inventory classifications table

Revision ID: c8329b8cc5e7
Revises: b4f8fb1c1e5d
Create Date: 2025-11-14 20:25:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c8329b8cc5e7"
down_revision: Union[str, Sequence[str], None] = "b4f8fb1c1e5d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "inventory_classifications",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("produits.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("abc_class", sa.String(length=1), nullable=False, server_default="C"),
        sa.Column("xyz_class", sa.String(length=1), nullable=False, server_default="Z"),
        sa.Column("value_share", sa.Numeric(10, 4), nullable=True),
        sa.Column("annual_consumption_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("cv", sa.Numeric(10, 4), nullable=True),
        sa.Column("demand_mean", sa.Numeric(12, 4), nullable=True),
        sa.Column("demand_std", sa.Numeric(12, 4), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "product_id", name="uq_inventory_classification_product"),
    )
    op.create_index(
        "ix_inventory_classifications_tenant",
        "inventory_classifications",
        ["tenant_id", "abc_class", "xyz_class"],
    )


def downgrade() -> None:
    op.drop_index("ix_inventory_classifications_tenant", table_name="inventory_classifications")
    op.drop_table("inventory_classifications")
