"""Ajoute la colonne produit_id sur produits_price_history pour l'historique des prix."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251213_produits_price_history_produit_id"
down_revision = "20251213_finance_matches_fk_lines"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "produits_price_history",
        sa.Column("produit_id", sa.Integer(), nullable=True),
    )
    # Index pour accélérer les recherches par produit
    op.execute("CREATE INDEX IF NOT EXISTS ix_produits_price_history_produit_id ON produits_price_history (produit_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_produits_price_history_produit_id")
    op.drop_column("produits_price_history", "produit_id")
