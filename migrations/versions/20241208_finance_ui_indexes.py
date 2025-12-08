"""Add performance indexes for finance UI."""

from alembic import op

revision = "20241208_finance_ui_idx"
down_revision = "20241207_app_users_tenant"
branch_labels = None
depends_on = None


def upgrade():
    # Bank statements indexes
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_finance_bank_stmts_account_period_status
        ON finance_bank_statements(account_id, period_start, period_end);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_finance_bank_stmt_lines_stmt_date
        ON finance_bank_statement_lines(statement_id, date_operation);
    """)

    # Invoices indexes
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_finance_invoices_entity_status_due
        ON finance_invoices_supplier(entity_id, status, date_due);
    """)

    # Vendors indexes
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_finance_vendors_entity_active
        ON finance_vendors(entity_id, is_active);
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_finance_vendors_entity_active;")
    op.execute("DROP INDEX IF EXISTS ix_finance_invoices_entity_status_due;")
    op.execute("DROP INDEX IF EXISTS ix_finance_bank_stmt_lines_stmt_date;")
    op.execute("DROP INDEX IF EXISTS ix_finance_bank_stmts_account_period_status;")
