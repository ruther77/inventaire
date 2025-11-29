"""add_fact_layer

Revision ID: 09f118fbd720
Revises: 9e3c7d947fd7
Create Date: 2025-11-14 16:04:44.958523

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '09f118fbd720'
down_revision: Union[str, Sequence[str], None] = '9e3c7d947fd7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create consolidation dimensions and fact tables."""

    op.create_table(
        'dim_date',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('date_value', sa.Date(), unique=True, nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('quarter', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('day', sa.Integer(), nullable=False),
        sa.Column('week', sa.Integer(), nullable=False),
    )

    op.create_table(
        'dim_tenant',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.Text(), nullable=False, unique=True),
        sa.Column('name', sa.Text(), nullable=False),
    )

    op.create_table(
        'dim_category',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.Text(), nullable=False, unique=True),
        sa.Column('label', sa.Text(), nullable=False),
    )

    op.create_table(
        'dim_supplier',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.Text(), nullable=True, unique=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('iban', sa.Text(), nullable=True),
    )

    op.create_table(
        'dim_product',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('sku', sa.Text(), nullable=True, unique=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('barcode', sa.Text(), nullable=True, unique=True),
        sa.Column('default_category_id', sa.Integer(), sa.ForeignKey('dim_category.id'), nullable=True),
    )

    op.create_table(
        'fact_transactions',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('dim_tenant.id'), nullable=False),
        sa.Column('date_id', sa.Integer(), sa.ForeignKey('dim_date.id'), nullable=False),
        sa.Column('supplier_id', sa.Integer(), sa.ForeignKey('dim_supplier.id'), nullable=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('dim_category.id'), nullable=True),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='EUR'),
        sa.Column('source_account', sa.Text(), nullable=True),
        sa.Column('direction', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
    )
    op.create_index('ix_fact_transactions_tenant_date', 'fact_transactions', ['tenant_id', 'date_id'])

    op.create_table(
        'fact_invoices',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('dim_tenant.id'), nullable=False),
        sa.Column('date_id', sa.Integer(), sa.ForeignKey('dim_date.id'), nullable=False),
        sa.Column('supplier_id', sa.Integer(), sa.ForeignKey('dim_supplier.id'), nullable=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('dim_product.id'), nullable=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('dim_category.id'), nullable=True),
        sa.Column('invoice_number', sa.Text(), nullable=True),
        sa.Column('sku', sa.Text(), nullable=True),
        sa.Column('quantity', sa.Numeric(14, 3), nullable=False, server_default='1'),
        sa.Column('unit_cost_excl_tax', sa.Numeric(14, 4), nullable=False, server_default='0'),
        sa.Column('vat_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='EUR'),
    )
    op.create_index('ix_fact_invoices_tenant_date', 'fact_invoices', ['tenant_id', 'date_id'])

    op.create_table(
        'fact_sales',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('dim_tenant.id'), nullable=False),
        sa.Column('date_id', sa.Integer(), sa.ForeignKey('dim_date.id'), nullable=False),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('dim_product.id'), nullable=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('dim_category.id'), nullable=True),
        sa.Column('channel', sa.Text(), nullable=True),
        sa.Column('quantity', sa.Numeric(14, 3), nullable=False, server_default='0'),
        sa.Column('net_amount', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('vat_amount', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('metadata', sa.JSON(), nullable=True),
    )
    op.create_index('ix_fact_sales_tenant_date', 'fact_sales', ['tenant_id', 'date_id'])


def downgrade() -> None:
    """Drop consolidation tables in reverse order."""

    op.drop_index('ix_fact_sales_tenant_date', table_name='fact_sales')
    op.drop_table('fact_sales')

    op.drop_index('ix_fact_invoices_tenant_date', table_name='fact_invoices')
    op.drop_table('fact_invoices')

    op.drop_index('ix_fact_transactions_tenant_date', table_name='fact_transactions')
    op.drop_table('fact_transactions')

    op.drop_table('dim_product')
    op.drop_table('dim_supplier')
    op.drop_table('dim_category')
    op.drop_table('dim_tenant')
    op.drop_table('dim_date')
