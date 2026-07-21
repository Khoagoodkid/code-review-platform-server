"""empty message

Revision ID: 552d1d5c3e42
Revises: 97c8fd24e68c
Create Date: 2026-06-14 19:49:25.831368

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '552d1d5c3e42'
down_revision: Union[str, Sequence[str], None] = '97c8fd24e68c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
