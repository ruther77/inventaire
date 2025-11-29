"""finance entities mapping

Revision ID: e32e12bd5139
Revises: d72cb3da9a7c
Create Date: 2025-11-14 21:05:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e32e12bd5139"
down_revision: Union[str, Sequence[str], None] = "d72cb3da9a7c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "finance_entities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.Text(), nullable=False, unique=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "finance_entity_members",
        sa.Column("entity_id", sa.Integer(), sa.ForeignKey("finance_entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("entity_id", "tenant_id", name="uq_finance_entity_member"),
    )
    op.create_index("ix_finance_entity_member_tenant", "finance_entity_members", ["tenant_id"])

    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO finance_entities (code, name)
            SELECT code, name FROM tenants
            ON CONFLICT (code) DO NOTHING
            """
        )
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO finance_entity_members (entity_id, tenant_id)
            SELECT fe.id, t.id
            FROM finance_entities fe
            JOIN tenants t ON t.code = fe.code
            ON CONFLICT DO NOTHING
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_finance_entity_member_tenant", table_name="finance_entity_members")
    op.drop_table("finance_entity_members")
    op.drop_table("finance_entities")
