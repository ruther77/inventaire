"""Merge heads

Revision ID: b62f12b01988
Revises: 20251211_zero_click_jobs, 20251214_newcms_finance_classification
Create Date: 2025-12-12 00:11:35.237887
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b62f12b01988'
down_revision = ('20251211_zero_click_jobs', '20251214_newcms_finance_classification')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
