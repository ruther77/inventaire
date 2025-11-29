"""ajout nouvelle vue

Revision ID: ba1f96ef4dfd
Revises: 5ff57783ea01
Create Date: 2025-11-08 17:25:32.174327

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba1f96ef4dfd'
down_revision: Union[str, Sequence[str], None] = '5ff57783ea01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create audit tables used by diagnostics and workflows."""

    op.create_table(
        'audit_actions',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('product_id', sa.Integer, sa.ForeignKey('produits.id', ondelete='CASCADE'), nullable=False),
        sa.Column('responsable', sa.Text, nullable=False),
        sa.Column('note', sa.Text),
        sa.Column('status', sa.Text, server_default=sa.text("'A investiguer'")),
        sa.Column('due_date', sa.Date),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
    )

    op.create_table(
        'audit_resolution_log',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('action_id', sa.Integer, sa.ForeignKey('audit_actions.id', ondelete='CASCADE')),
        sa.Column('product_id', sa.Integer, sa.ForeignKey('produits.id', ondelete='CASCADE'), nullable=False),
        sa.Column('statut', sa.Text, nullable=False),
        sa.Column('note', sa.Text),
        sa.Column('responsable', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
    )

    op.create_index('idx_audit_actions_product', 'audit_actions', ['product_id'])
    op.create_index('idx_audit_actions_status', 'audit_actions', ['status'])
    op.create_index('idx_audit_log_product', 'audit_resolution_log', ['product_id'])
    op.create_index('idx_audit_log_action', 'audit_resolution_log', ['action_id'])


def downgrade() -> None:
    """Drop audit tables."""

    op.drop_index('idx_audit_log_action', table_name='audit_resolution_log')
    op.drop_index('idx_audit_log_product', table_name='audit_resolution_log')
    op.drop_table('audit_resolution_log')

    op.drop_index('idx_audit_actions_status', table_name='audit_actions')
    op.drop_index('idx_audit_actions_product', table_name='audit_actions')
    op.drop_table('audit_actions')
