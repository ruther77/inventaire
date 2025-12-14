"""Ajout des tables CMS (cms_pages et cms_nav_items) pour le nouveau système de gestion de contenu.

Revision ID: 20251211_cms_tables
Revises: 20251213_produits_price_history_produit_id
Create Date: 2025-12-11
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251211_cms_tables"
down_revision = "20251213_produits_price_history_produit_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Table cms_pages : stocke les pages de contenu
    op.create_table(
        "cms_pages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "slug", name="uq_cms_pages_tenant_slug"),
    )

    # Index pour recherche par tenant et statut
    op.create_index("ix_cms_pages_tenant_id", "cms_pages", ["tenant_id"])
    op.create_index("ix_cms_pages_status", "cms_pages", ["status"])
    op.create_index("ix_cms_pages_updated_at", "cms_pages", ["updated_at"])

    # Table cms_nav_items : stocke les éléments de navigation
    op.create_table(
        "cms_nav_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("section", sa.String(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("icon", sa.String(), nullable=True),
        sa.Column("badge", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
    )

    # Index pour recherche par tenant et tri
    op.create_index("ix_cms_nav_items_tenant_id", "cms_nav_items", ["tenant_id"])
    op.create_index("ix_cms_nav_items_section_order", "cms_nav_items", ["section", "order_index"])


def downgrade() -> None:
    # Suppression des index
    op.drop_index("ix_cms_nav_items_section_order", table_name="cms_nav_items")
    op.drop_index("ix_cms_nav_items_tenant_id", table_name="cms_nav_items")

    op.drop_index("ix_cms_pages_updated_at", table_name="cms_pages")
    op.drop_index("ix_cms_pages_status", table_name="cms_pages")
    op.drop_index("ix_cms_pages_tenant_id", table_name="cms_pages")

    # Suppression des tables
    op.drop_table("cms_nav_items")
    op.drop_table("cms_pages")
