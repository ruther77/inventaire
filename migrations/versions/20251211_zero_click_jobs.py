"""Ajout de la table zero_click_jobs pour le système de jobs async.

Revision ID: 20251211_zero_click_jobs
Revises: 20251211_cms_tables
Create Date: 2025-12-11
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251211_zero_click_jobs"
down_revision = "20251211_cms_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Table zero_click_jobs : stocke l'état des jobs async pour zero-click import
    op.create_table(
        "zero_click_jobs",
        sa.Column("job_id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("filename", sa.String(), nullable=True),
        sa.Column("supplier_hint", sa.String(), nullable=True),
        sa.Column("margin_percent", sa.Float(), nullable=False, server_default="40.0"),
        sa.Column("auto_confirm", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("job_id"),
    )

    # Index pour recherche rapide par tenant et statut
    op.create_index("ix_zero_click_jobs_tenant_id", "zero_click_jobs", ["tenant_id"])
    op.create_index("ix_zero_click_jobs_status", "zero_click_jobs", ["status"])
    op.create_index("ix_zero_click_jobs_created_at", "zero_click_jobs", ["created_at"])
    op.create_index("ix_zero_click_jobs_tenant_status", "zero_click_jobs", ["tenant_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_zero_click_jobs_tenant_status", table_name="zero_click_jobs")
    op.drop_index("ix_zero_click_jobs_created_at", table_name="zero_click_jobs")
    op.drop_index("ix_zero_click_jobs_status", table_name="zero_click_jobs")
    op.drop_index("ix_zero_click_jobs_tenant_id", table_name="zero_click_jobs")
    op.drop_table("zero_click_jobs")
