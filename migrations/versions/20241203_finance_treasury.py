"""Refonte trésorerie transverse (comptes, transactions, factures, relevés)."""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20241203_finance_treasury"
down_revision: Union[str, Sequence[str], None] = "202501_restaurant_sales_stock"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_enum(enum_name: str, values: list[str]) -> None:
    values_sql = ", ".join(f"'{value}'" for value in values)
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{enum_name}') THEN
                CREATE TYPE {enum_name} AS ENUM ({values_sql});
            END IF;
        END
        $$;
        """
    )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    account_type_enum = postgresql.ENUM(
        "BANQUE",
        "CAISSE",
        "CB",
        "AUTRE",
        "PLATFORM",
        name="finance_account_type",
        create_type=False,
    )
    tx_direction_enum = postgresql.ENUM(
        "IN",
        "OUT",
        "TRANSFER",
        name="finance_tx_direction",
        create_type=False,
    )
    tx_status_enum = postgresql.ENUM(
        "DRAFT",
        "CONFIRMED",
        "CANCELLED",
        name="finance_tx_status",
        create_type=False,
    )

    finance_entities_columns = {col["name"] for col in inspector.get_columns("finance_entities")}

    # Harmonise finance_entities to the richer schema (currency/activation/audit).
    op.drop_constraint("finance_entity_members_entity_id_fkey", "finance_entity_members", type_="foreignkey")
    op.execute("ALTER TABLE finance_entities ALTER COLUMN id TYPE BIGINT USING id::BIGINT")
    op.alter_column(
        "finance_entity_members",
        "entity_id",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        nullable=False,
    )
    op.create_foreign_key(
        "finance_entity_members_entity_id_fkey",
        "finance_entity_members",
        "finance_entities",
        ["entity_id"],
        ["id"],
        ondelete="CASCADE",
    )
    if "currency" not in finance_entities_columns:
        op.add_column("finance_entities", sa.Column("currency", sa.Text(), nullable=False, server_default="EUR"))
    if "is_active" not in finance_entities_columns:
        op.add_column(
            "finance_entities",
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.sql.expression.true()),
        )
    if "updated_at" not in finance_entities_columns:
        op.add_column(
            "finance_entities",
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
    existing_fe_indexes = {idx["name"] for idx in inspector.get_indexes("finance_entities")}
    if "ix_finance_entities_is_active" not in existing_fe_indexes:
        op.create_index("ix_finance_entities_is_active", "finance_entities", ["is_active"])
    if "ix_finance_entities_name" not in existing_fe_indexes:
        op.create_index("ix_finance_entities_name", "finance_entities", ["name"])

    # finance_entity_members: add technical PK.
    fem_columns = {col["name"] for col in inspector.get_columns("finance_entity_members")}
    if "id" not in fem_columns:
        op.execute(
            """
            ALTER TABLE finance_entity_members ADD COLUMN id BIGSERIAL;
            UPDATE finance_entity_members SET id = nextval('finance_entity_members_id_seq') WHERE id IS NULL;
            ALTER TABLE finance_entity_members ADD PRIMARY KEY (id);
            """
        )

    # Enums required by the new finance domain.
    _create_enum("finance_account_type", ["BANQUE", "CAISSE", "CB", "AUTRE", "PLATFORM"])
    _create_enum("finance_tx_direction", ["IN", "OUT", "TRANSFER"])
    _create_enum("finance_tx_status", ["DRAFT", "CONFIRMED", "CANCELLED"])

    op.create_table(
        "finance_categories",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("entity_id", sa.BigInteger(), sa.ForeignKey("finance_entities.id"), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("parent_id", sa.BigInteger(), sa.ForeignKey("finance_categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("entity_id", "code", name="uq_finance_categories_entity_code"),
    )
    op.create_index("ix_finance_categories_parent", "finance_categories", ["parent_id"])
    op.create_index("ix_finance_categories_entity_type", "finance_categories", ["entity_id", "type"])

    op.create_table(
        "finance_cost_centers",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("entity_id", sa.BigInteger(), sa.ForeignKey("finance_entities.id"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.sql.expression.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("entity_id", "code", name="uq_finance_cost_centers_entity_code"),
    )
    op.create_index("ix_finance_cost_centers_active", "finance_cost_centers", ["entity_id", "is_active"])

    op.create_table(
        "finance_accounts",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("entity_id", sa.BigInteger(), sa.ForeignKey("finance_entities.id"), nullable=False),
        sa.Column("type", account_type_enum, nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("iban", sa.Text(), nullable=True),
        sa.Column("bic", sa.Text(), nullable=True),
        sa.Column("currency", sa.Text(), nullable=False, server_default="EUR"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.sql.expression.true()),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("iban", name="uq_finance_accounts_iban"),
    )
    op.create_index("ix_finance_accounts_entity_type", "finance_accounts", ["entity_id", "type"])
    op.create_index("ix_finance_accounts_active", "finance_accounts", ["is_active"])

    op.create_table(
        "finance_account_balances",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("account_id", sa.BigInteger(), sa.ForeignKey("finance_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("balance", sa.Numeric(18, 2), nullable=False),
        sa.Column("source", sa.Text(), nullable=False, server_default="COMPUTED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("account_id", "date", name="uq_finance_account_balances_account_date"),
    )
    op.create_index("ix_finance_account_balances_date", "finance_account_balances", ["date"])

    op.create_table(
        "finance_transactions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("entity_id", sa.BigInteger(), sa.ForeignKey("finance_entities.id"), nullable=False),
        sa.Column("account_id", sa.BigInteger(), sa.ForeignKey("finance_accounts.id"), nullable=False),
        sa.Column("counterparty_account_id", sa.BigInteger(), sa.ForeignKey("finance_accounts.id"), nullable=True),
        sa.Column("direction", tx_direction_enum, nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("date_operation", sa.Date(), nullable=False),
        sa.Column("date_value", sa.Date(), nullable=True),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.Text(), nullable=False, server_default="EUR"),
        sa.Column("ref_externe", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("status", tx_status_enum, nullable=False, server_default="CONFIRMED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("ref_externe", name="uq_finance_transactions_ref_externe"),
    )
    op.create_index("ix_finance_transactions_entity_date", "finance_transactions", ["entity_id", "date_operation"])
    op.create_index("ix_finance_transactions_account_date", "finance_transactions", ["account_id", "date_operation"])

    op.create_table(
        "finance_transaction_lines",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "transaction_id",
            sa.BigInteger(),
            sa.ForeignKey("finance_transactions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category_id", sa.BigInteger(), sa.ForeignKey("finance_categories.id"), nullable=False),
        sa.Column("cost_center_id", sa.BigInteger(), sa.ForeignKey("finance_cost_centers.id"), nullable=True),
        sa.Column("montant_ht", sa.Numeric(18, 2), nullable=True),
        sa.Column("tva_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("montant_ttc", sa.Numeric(18, 2), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index("ix_finance_transaction_lines_transaction", "finance_transaction_lines", ["transaction_id"])
    op.create_index("ix_finance_transaction_lines_category", "finance_transaction_lines", ["category_id"])
    op.create_index("ix_finance_transaction_lines_cost_center", "finance_transaction_lines", ["cost_center_id"])

    op.create_table(
        "finance_vendors",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("entity_id", sa.BigInteger(), sa.ForeignKey("finance_entities.id"), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("siret", sa.Text(), nullable=True),
        sa.Column("iban", sa.Text(), nullable=True),
        sa.Column("bic", sa.Text(), nullable=True),
        sa.Column("contact_email", sa.Text(), nullable=True),
        sa.Column("contact_phone", sa.Text(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.sql.expression.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("entity_id", "name", name="uq_finance_vendors_entity_name"),
    )
    op.create_index("ix_finance_vendors_entity_name", "finance_vendors", ["entity_id", "name"])

    op.create_table(
        "finance_invoices_supplier",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("entity_id", sa.BigInteger(), sa.ForeignKey("finance_entities.id"), nullable=False),
        sa.Column("vendor_id", sa.BigInteger(), sa.ForeignKey("finance_vendors.id"), nullable=False),
        sa.Column("invoice_number", sa.Text(), nullable=False),
        sa.Column("date_invoice", sa.Date(), nullable=True),
        sa.Column("date_due", sa.Date(), nullable=True),
        sa.Column("montant_ht", sa.Numeric(18, 2), nullable=True),
        sa.Column("montant_tva", sa.Numeric(18, 2), nullable=True),
        sa.Column("montant_ttc", sa.Numeric(18, 2), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="EN_ATTENTE"),
        sa.Column("source", sa.Text(), nullable=True),
        sa.Column("currency", sa.Text(), nullable=False, server_default="EUR"),
        sa.Column("ref_externe", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("entity_id", "vendor_id", "invoice_number", name="uq_finance_invoices_supplier_unique"),
    )
    op.create_index("ix_finance_invoices_supplier_status", "finance_invoices_supplier", ["status"])
    op.create_index("ix_finance_invoices_supplier_due", "finance_invoices_supplier", ["date_due"])

    op.create_table(
        "finance_invoice_lines_supplier",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "invoice_id",
            sa.BigInteger(),
            sa.ForeignKey("finance_invoices_supplier.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category_id", sa.BigInteger(), sa.ForeignKey("finance_categories.id"), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("quantite", sa.Numeric(12, 3), nullable=True),
        sa.Column("prix_unitaire", sa.Numeric(18, 4), nullable=True),
        sa.Column("montant_ht", sa.Numeric(18, 2), nullable=True),
        sa.Column("tva_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("montant_ttc", sa.Numeric(18, 2), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index("ix_finance_invoice_lines_supplier_invoice", "finance_invoice_lines_supplier", ["invoice_id"])
    op.create_index("ix_finance_invoice_lines_supplier_category", "finance_invoice_lines_supplier", ["category_id"])

    op.create_table(
        "finance_payments",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("invoice_id", sa.BigInteger(), sa.ForeignKey("finance_invoices_supplier.id", ondelete="SET NULL"), nullable=True),
        sa.Column("transaction_id", sa.BigInteger(), sa.ForeignKey("finance_transactions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("date_payment", sa.Date(), nullable=False),
        sa.Column("mode", sa.Text(), nullable=False),
        sa.Column("currency", sa.Text(), nullable=False, server_default="EUR"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_finance_payments_invoice", "finance_payments", ["invoice_id"])
    op.create_index("ix_finance_payments_transaction", "finance_payments", ["transaction_id"])

    op.create_table(
        "finance_bank_statements",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("account_id", sa.BigInteger(), sa.ForeignKey("finance_accounts.id"), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("file_name", sa.Text(), nullable=True),
        sa.Column("hash", sa.Text(), nullable=True),
    )
    op.create_index("ix_finance_bank_statements_account_period", "finance_bank_statements", ["account_id", "period_start"])
    op.create_unique_constraint(
        "uq_finance_bank_statements_account_hash",
        "finance_bank_statements",
        ["account_id", "hash"],
    )

    op.create_table(
        "finance_bank_statement_lines",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "statement_id",
            sa.BigInteger(),
            sa.ForeignKey("finance_bank_statements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date_operation", sa.Date(), nullable=False),
        sa.Column("date_valeur", sa.Date(), nullable=True),
        sa.Column("libelle_banque", sa.Text(), nullable=True),
        sa.Column("montant", sa.Numeric(18, 2), nullable=False),
        sa.Column("balance_apres", sa.Numeric(18, 2), nullable=True),
        sa.Column("ref_banque", sa.Text(), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(), nullable=True),
        sa.Column("checksum", sa.Text(), nullable=True),
    )
    op.create_index("ix_finance_bank_statement_lines_statement", "finance_bank_statement_lines", ["statement_id"])
    op.create_index("ix_finance_bank_statement_lines_ref_banque", "finance_bank_statement_lines", ["ref_banque"])
    op.create_index("ix_finance_bank_statement_lines_checksum", "finance_bank_statement_lines", ["checksum"])

    op.create_table(
        "finance_reconciliations",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "statement_line_id",
            sa.BigInteger(),
            sa.ForeignKey("finance_bank_statement_lines.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "transaction_id",
            sa.BigInteger(),
            sa.ForeignKey("finance_transactions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.Text(), nullable=False, server_default="AUTO"),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.UniqueConstraint("statement_line_id", name="uq_finance_reconciliations_statement_line"),
    )
    op.create_index("ix_finance_reconciliations_transaction", "finance_reconciliations", ["transaction_id"])
    op.create_index("ix_finance_reconciliations_status", "finance_reconciliations", ["status"])

    # capital_snapshot: multi-entité.
    capital_columns = {col["name"] for col in inspector.get_columns("capital_snapshot")}
    if "entity_id" not in capital_columns:
        op.add_column("capital_snapshot", sa.Column("entity_id", sa.BigInteger(), nullable=True))
        op.create_foreign_key(
            "fk_capital_snapshot_entity",
            "capital_snapshot",
            "finance_entities",
            ["entity_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.execute(
            """
            UPDATE capital_snapshot cs
            SET entity_id = fe.id
            FROM tenants t
            JOIN finance_entities fe ON fe.code = t.code
            WHERE cs.tenant_id = t.id
            """
        )
    existing_capital_indexes = {idx["name"] for idx in inspector.get_indexes("capital_snapshot")}
    if "idx_capital_snapshot_tenant_date" in existing_capital_indexes:
        op.drop_index("idx_capital_snapshot_tenant_date", table_name="capital_snapshot")
    existing_capital_uniques = {uc["name"] for uc in inspector.get_unique_constraints("capital_snapshot")}
    if "ux_capital_snapshot_tenant_date" in existing_capital_uniques:
        op.drop_constraint("ux_capital_snapshot_tenant_date", "capital_snapshot", type_="unique")
    if "ux_capital_snapshot_entity_date" not in existing_capital_uniques:
        op.create_unique_constraint(
            "ux_capital_snapshot_entity_date",
            "capital_snapshot",
            ["entity_id", "snapshot_date"],
        )
    if "idx_capital_snapshot_entity_date" not in existing_capital_indexes:
        op.create_index(
            "idx_capital_snapshot_entity_date",
            "capital_snapshot",
            ["entity_id", "snapshot_date"],
        )


def downgrade() -> None:
    # Drop finance domain tables in reverse dependency order.
    op.drop_index("ix_finance_reconciliations_status", table_name="finance_reconciliations")
    op.drop_index("ix_finance_reconciliations_transaction", table_name="finance_reconciliations")
    op.drop_table("finance_reconciliations")

    op.drop_index("ix_finance_bank_statement_lines_checksum", table_name="finance_bank_statement_lines")
    op.drop_index("ix_finance_bank_statement_lines_ref_banque", table_name="finance_bank_statement_lines")
    op.drop_index("ix_finance_bank_statement_lines_statement", table_name="finance_bank_statement_lines")
    op.drop_table("finance_bank_statement_lines")

    op.drop_constraint("uq_finance_bank_statements_account_hash", "finance_bank_statements", type_="unique")
    op.drop_index("ix_finance_bank_statements_account_period", table_name="finance_bank_statements")
    op.drop_table("finance_bank_statements")

    op.drop_index("ix_finance_payments_transaction", table_name="finance_payments")
    op.drop_index("ix_finance_payments_invoice", table_name="finance_payments")
    op.drop_table("finance_payments")

    op.drop_index("ix_finance_invoice_lines_supplier_category", table_name="finance_invoice_lines_supplier")
    op.drop_index("ix_finance_invoice_lines_supplier_invoice", table_name="finance_invoice_lines_supplier")
    op.drop_table("finance_invoice_lines_supplier")

    op.drop_index("ix_finance_invoices_supplier_due", table_name="finance_invoices_supplier")
    op.drop_index("ix_finance_invoices_supplier_status", table_name="finance_invoices_supplier")
    op.drop_table("finance_invoices_supplier")

    op.drop_index("ix_finance_vendors_entity_name", table_name="finance_vendors")
    op.drop_table("finance_vendors")

    op.drop_index("ix_finance_transaction_lines_cost_center", table_name="finance_transaction_lines")
    op.drop_index("ix_finance_transaction_lines_category", table_name="finance_transaction_lines")
    op.drop_index("ix_finance_transaction_lines_transaction", table_name="finance_transaction_lines")
    op.drop_table("finance_transaction_lines")

    op.drop_index("ix_finance_transactions_account_date", table_name="finance_transactions")
    op.drop_index("ix_finance_transactions_entity_date", table_name="finance_transactions")
    op.drop_table("finance_transactions")

    op.drop_index("ix_finance_account_balances_date", table_name="finance_account_balances")
    op.drop_table("finance_account_balances")

    op.drop_index("ix_finance_accounts_active", table_name="finance_accounts")
    op.drop_index("ix_finance_accounts_entity_type", table_name="finance_accounts")
    op.drop_table("finance_accounts")

    op.drop_index("ix_finance_cost_centers_active", table_name="finance_cost_centers")
    op.drop_table("finance_cost_centers")

    op.drop_index("ix_finance_categories_entity_type", table_name="finance_categories")
    op.drop_index("ix_finance_categories_parent", table_name="finance_categories")
    op.drop_table("finance_categories")

    # Capital snapshot rollback to tenant-based unique/index.
    op.drop_index("idx_capital_snapshot_entity_date", table_name="capital_snapshot")
    op.drop_constraint("ux_capital_snapshot_entity_date", "capital_snapshot", type_="unique")
    op.drop_constraint("fk_capital_snapshot_entity", "capital_snapshot", type_="foreignkey")
    op.drop_column("capital_snapshot", "entity_id")
    op.create_index("idx_capital_snapshot_tenant_date", "capital_snapshot", ["tenant_id", "snapshot_date"])
    op.create_unique_constraint(
        "ux_capital_snapshot_tenant_date",
        "capital_snapshot",
        ["tenant_id", "snapshot_date"],
    )

    # finance_entity_members PK column is kept (dropping it would require resequencing); only revert FK type.
    with op.batch_alter_table("finance_entity_members") as batch_op:
        batch_op.drop_constraint("finance_entity_members_entity_id_fkey", type_="foreignkey")
        batch_op.alter_column("entity_id", existing_type=sa.BigInteger(), type_=sa.Integer(), nullable=False)
        batch_op.create_foreign_key(
            "finance_entity_members_entity_id_fkey",
            "finance_entities",
            ["entity_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # finance_entities indexes/columns cleanup
    op.drop_index("ix_finance_entities_name", table_name="finance_entities")
    op.drop_index("ix_finance_entities_is_active", table_name="finance_entities")
    with op.batch_alter_table("finance_entities") as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.drop_column("is_active")
        batch_op.drop_column("currency")
        batch_op.alter_column("id", existing_type=sa.BigInteger(), type_=sa.Integer(), existing_nullable=False)

    # Drop finance enums last.
    op.execute("DROP TYPE IF EXISTS finance_tx_status")
    op.execute("DROP TYPE IF EXISTS finance_tx_direction")
    op.execute("DROP TYPE IF EXISTS finance_account_type")
