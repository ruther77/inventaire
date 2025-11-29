"""Create restaurant-specific tables (charges, ingrédients, plats)."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "202311_restaurant"
down_revision = "202310_multi_tenant"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "restaurant_depense_categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("nom", sa.Text(), nullable=False),
        sa.UniqueConstraint("tenant_id", "nom"),
    )

    op.create_table(
        "restaurant_cost_centers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("nom", sa.Text(), nullable=False),
        sa.UniqueConstraint("tenant_id", "nom"),
    )

    op.create_table(
        "restaurant_fournisseurs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("nom", sa.Text(), nullable=False),
        sa.Column("iban", sa.Text()),
        sa.Column("siret", sa.Text()),
        sa.UniqueConstraint("tenant_id", "nom"),
    )

    op.create_table(
        "restaurant_depenses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("categorie_id", sa.Integer(), sa.ForeignKey("restaurant_depense_categories.id")),
        sa.Column("fournisseur_id", sa.Integer(), sa.ForeignKey("restaurant_fournisseurs.id")),
        sa.Column("cost_center_id", sa.Integer(), sa.ForeignKey("restaurant_cost_centers.id")),
        sa.Column("libelle", sa.Text(), nullable=False),
        sa.Column("unite", sa.Text()),
        sa.Column("quantite", sa.Numeric(14, 4)),
        sa.Column("prix_unitaire", sa.Numeric(12, 4)),
        sa.Column("montant_ht", sa.Numeric(12, 2)),
        sa.Column("tva_pct", sa.Numeric(5, 2), server_default="20.0"),
        sa.Column("date_operation", sa.Date(), server_default=sa.func.current_date()),
        sa.Column("source", sa.Text()),
        sa.Column("ref_externe", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "restaurant_ingredients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("nom", sa.Text(), nullable=False),
        sa.Column("unite_base", sa.Text(), nullable=False, server_default="kg"),
        sa.Column("cout_unitaire", sa.Numeric(12, 4), server_default="0"),
        sa.Column("stock_actuel", sa.Numeric(14, 4), server_default="0"),
        sa.UniqueConstraint("tenant_id", "nom"),
    )

    op.create_table(
        "restaurant_plats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("nom", sa.Text(), nullable=False),
        sa.Column("categorie", sa.Text()),
        sa.Column("prix_vente_ttc", sa.Numeric(12, 2), server_default="0"),
        sa.Column("actif", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("tenant_id", "nom"),
    )

    op.create_table(
        "restaurant_plat_ingredients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("plat_id", sa.Integer(), sa.ForeignKey("restaurant_plats.id", ondelete="CASCADE")),
        sa.Column("ingredient_id", sa.Integer(), sa.ForeignKey("restaurant_ingredients.id", ondelete="CASCADE")),
        sa.Column("quantite", sa.Numeric(14, 4), nullable=False),
        sa.Column("unite", sa.Text()),
        sa.UniqueConstraint("plat_id", "ingredient_id"),
    )


def downgrade() -> None:
    for table in (
        "restaurant_plat_ingredients",
        "restaurant_plats",
        "restaurant_ingredients",
        "restaurant_depenses",
        "restaurant_fournisseurs",
        "restaurant_cost_centers",
        "restaurant_depense_categories",
    ):
        op.drop_table(table)
