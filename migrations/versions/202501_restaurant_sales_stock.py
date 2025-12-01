"""Add restaurant sales table and consumption view."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "202501_restaurant_sales_stock"
down_revision = "f2a1e6a1a3b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "restaurant_sales",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("plat_id", sa.Integer(), sa.ForeignKey("restaurant_plats.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("sold_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("source", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_restaurant_sales_tenant_plat",
        "restaurant_sales",
        ["tenant_id", "plat_id", "sold_at"],
    )

    op.execute(
        """
        CREATE VIEW restaurant_sales_consumptions AS
        SELECT
            s.tenant_id,
            map.produit_restaurant_id,
            map.produit_epicerie_id,
            COALESCE(p.nom, '') AS epicerie_nom,
            COALESCE(p.categorie, '') AS epicerie_categorie,
            COALESCE(p.prix_achat, 0) AS prix_achat,
            COALESCE(p.prix_vente, 0) AS prix_vente,
            COALESCE(p.stock_actuel, 0) AS stock_actuel,
            COALESCE(SUM(s.quantity * COALESCE(map.ratio, 1)), 0) AS quantity_consumed,
            CEIL(COALESCE(SUM(s.quantity * COALESCE(map.ratio, 1)), 0)) AS bottles_required,
            COALESCE(SUM(s.quantity * COALESCE(map.ratio, 1) * COALESCE(p.prix_achat, 0)), 0) AS cost_spent,
            COALESCE(p.stock_actuel, 0) - COALESCE(SUM(s.quantity * COALESCE(map.ratio, 1)), 0) AS stock_after_sales,
            MAX(s.sold_at) AS last_sale_at
        FROM restaurant_sales s
        JOIN restaurant_epicerie_sku_map map
            ON map.produit_restaurant_id = s.plat_id
            AND map.tenant_restaurant = s.tenant_id
        LEFT JOIN produits p
            ON p.id = map.produit_epicerie_id
            AND p.tenant_id = map.tenant_epicerie
        GROUP BY
            s.tenant_id,
            map.produit_restaurant_id,
            map.produit_epicerie_id,
            p.nom,
            p.categorie,
            p.prix_achat,
            p.prix_vente,
            p.stock_actuel;
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS restaurant_sales_consumptions")
    op.drop_index("ix_restaurant_sales_tenant_plat", table_name="restaurant_sales")
    op.drop_table("restaurant_sales")
