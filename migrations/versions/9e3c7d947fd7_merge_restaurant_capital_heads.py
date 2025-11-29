"""Merge restaurant & capital heads

Revision ID: 9e3c7d947fd7
Revises: 202311_restaurant, d5d0e6_capital_snapshot_index
Create Date: 2025-11-13 04:10:44.224583

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e3c7d947fd7'
down_revision: Union[str, Sequence[str], None] = ('202311_restaurant', 'd5d0e6_capital_snapshot_index')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
