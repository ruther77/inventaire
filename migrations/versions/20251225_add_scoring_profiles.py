"""Add supplier scoring profiles for dynamic weights.

Enables different scoring strategies for PME vs Grands Comptes.
Each profile defines custom weights for the 7 scoring dimensions.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "20251225_add_scoring_profiles"
down_revision: Union[str, Sequence[str], None] = "20251225_add_category_thresholds"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create supplier_scoring_profiles table
    op.create_table(
        "supplier_scoring_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        # Weights for 7 dimensions (must sum to 100)
        sa.Column("price_stability_weight", sa.Numeric(5, 2), nullable=False, server_default="25.0"),
        sa.Column("delivery_reliability_weight", sa.Numeric(5, 2), nullable=False, server_default="20.0"),
        sa.Column("invoice_accuracy_weight", sa.Numeric(5, 2), nullable=False, server_default="15.0"),
        sa.Column("stock_accuracy_weight", sa.Numeric(5, 2), nullable=False, server_default="15.0"),
        sa.Column("payment_terms_weight", sa.Numeric(5, 2), nullable=False, server_default="10.0"),
        sa.Column("responsiveness_weight", sa.Numeric(5, 2), nullable=False, server_default="10.0"),
        sa.Column("product_quality_weight", sa.Numeric(5, 2), nullable=False, server_default="5.0"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create indexes
    op.create_index(
        "idx_scoring_profiles_tenant",
        "supplier_scoring_profiles",
        ["tenant_id"]
    )
    op.create_index(
        "idx_scoring_profiles_default",
        "supplier_scoring_profiles",
        ["tenant_id", "is_default"]
    )

    # Add scoring_profile_id to dim_supplier
    op.add_column(
        "dim_supplier",
        sa.Column(
            "scoring_profile_id",
            sa.Integer(),
            sa.ForeignKey("supplier_scoring_profiles.id", ondelete="SET NULL"),
            nullable=True
        )
    )

    op.create_index(
        "idx_dim_supplier_profile",
        "dim_supplier",
        ["scoring_profile_id"]
    )

    # Seed default profiles
    bind = op.get_bind()

    # Note: We seed for tenant_id=1 as default, applications should create profiles for other tenants
    bind.execute(
        text("""
            INSERT INTO supplier_scoring_profiles (
                tenant_id, name, description,
                price_stability_weight, delivery_reliability_weight,
                invoice_accuracy_weight, stock_accuracy_weight,
                payment_terms_weight, responsiveness_weight,
                product_quality_weight, is_default
            ) VALUES
            -- PME Profile: Focus on price stability and delivery
            (1, 'PME', 'Profil pour PME - Focus sur stabilité prix et livraison',
             30.0, 25.0, 15.0, 10.0, 10.0, 5.0, 5.0, true),

            -- Grand Compte Profile: Focus on delivery, quality, and responsiveness
            (1, 'Grand Compte', 'Profil pour grands comptes - Focus sur livraison, qualité et réactivité',
             15.0, 30.0, 15.0, 10.0, 10.0, 15.0, 5.0, false),

            -- Quality Focused Profile: For critical products
            (1, 'Qualité Premium', 'Focus sur qualité et fiabilité',
             10.0, 25.0, 15.0, 15.0, 5.0, 10.0, 20.0, false),

            -- Price Focused Profile: For commodity items
            (1, 'Prix Compétitif', 'Focus sur stabilité des prix',
             40.0, 20.0, 10.0, 10.0, 10.0, 5.0, 5.0, false)
        """)
    )


def downgrade() -> None:
    op.drop_index("idx_dim_supplier_profile", table_name="dim_supplier")
    op.drop_column("dim_supplier", "scoring_profile_id")
    op.drop_index("idx_scoring_profiles_default", table_name="supplier_scoring_profiles")
    op.drop_index("idx_scoring_profiles_tenant", table_name="supplier_scoring_profiles")
    op.drop_table("supplier_scoring_profiles")
