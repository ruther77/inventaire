"""NewCMS finance classification and rule extensions."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251214_newcms_finance_classification"
down_revision = "20251213_produits_price_history_produit_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tables de staging import : ajouter invoice_date + error
    op.add_column("newcms_invoice_import_jobs", sa.Column("invoice_date", sa.Date(), nullable=True))
    op.add_column("newcms_invoice_import_lines", sa.Column("invoice_date", sa.Date(), nullable=True))
    op.add_column("newcms_invoice_import_lines", sa.Column("error", sa.Text(), nullable=True))

    # Table classification officielle
    op.create_table(
        "finance_transaction_classification",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("transaction_id", sa.BigInteger(), sa.ForeignKey("finance_transactions.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("category_id", sa.BigInteger(), sa.ForeignKey("finance_categories.id"), nullable=True),
        sa.Column("source", sa.Text(), nullable=False, server_default="manual"),
        sa.Column("rule_id", sa.BigInteger(), sa.ForeignKey("finance_rules.id"), nullable=True),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("ignored", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_finance_tx_classification_cat",
        "finance_transaction_classification",
        ["category_id"],
        unique=False,
    )

    # Extensions finance_rules
    op.add_column("finance_rules", sa.Column("amount_min", sa.Numeric(18, 2), nullable=True))
    op.add_column("finance_rules", sa.Column("amount_max", sa.Numeric(18, 2), nullable=True))
    op.add_column("finance_rules", sa.Column("regex_pattern", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("finance_rules", "regex_pattern")
    op.drop_column("finance_rules", "amount_max")
    op.drop_column("finance_rules", "amount_min")

    op.drop_index("ix_finance_tx_classification_cat", table_name="finance_transaction_classification")
    op.drop_table("finance_transaction_classification")

    op.drop_column("newcms_invoice_import_lines", "error")
    op.drop_column("newcms_invoice_import_lines", "invoice_date")
    op.drop_column("newcms_invoice_import_jobs", "invoice_date")
