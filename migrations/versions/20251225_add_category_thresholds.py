"""Add plat_categories table with target_food_cost_percent for category-based thresholds.

This migration creates the plat_categories table and seeds it with default values
for common restaurant categories (Entrées: 25%, Plats: 30%, Desserts: 35%).

The table links to restaurant_plats via the categorie TEXT field.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20251225_add_category_thresholds"
down_revision = "20251225_add_file_hash"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create plat_categories table
    op.create_table(
        "plat_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("nom", sa.Text(), nullable=False),
        sa.Column("target_food_cost_percent", sa.Numeric(5, 2), nullable=False, server_default="30.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "nom", name="uq_plat_categories_tenant_nom"),
    )

    # Create index for faster lookups
    op.create_index(
        "idx_plat_categories_tenant",
        "plat_categories",
        ["tenant_id"],
    )

    # Seed default categories with their target food cost percentages
    op.execute(
        """
        INSERT INTO plat_categories (tenant_id, nom, target_food_cost_percent)
        VALUES
            (1, 'Entrées', 25.0),
            (1, 'Plats', 30.0),
            (1, 'Desserts', 35.0),
            (1, 'Boissons', 20.0),
            (1, 'Apéritifs', 20.0),
            (1, 'Menus', 28.0),
            (1, 'Autres', 30.0)
        ON CONFLICT (tenant_id, nom) DO NOTHING
        """
    )


def downgrade() -> None:
    # Drop index
    op.drop_index("idx_plat_categories_tenant", table_name="plat_categories")

    # Drop table
    op.drop_table("plat_categories")
