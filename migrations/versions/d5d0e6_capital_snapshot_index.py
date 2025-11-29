"""Ajouter un index unique pour capital_snapshot."""

from alembic import op
import sqlalchemy as sa

revision = "d5d0e6_capital_snapshot_index"
down_revision = "c1d2f3_price_snapshot"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_unique_constraint(
        "ux_capital_snapshot_tenant_date",
        "capital_snapshot",
        ["tenant_id", "snapshot_date"],
    )

def downgrade() -> None:
    op.drop_constraint("ux_capital_snapshot_tenant_date", "capital_snapshot", type_="unique")
