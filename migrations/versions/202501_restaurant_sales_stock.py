"""Stub migration to anchor finance chain before treasury refonte."""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "202501_restaurant_sales_stock"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Cette migration est volontairement vide : elle sert uniquement
    # de point d'ancrage pour les migrations ultérieures (finance).
    pass


def downgrade() -> None:
    # Rien à supprimer, c'est un stub.
    pass
