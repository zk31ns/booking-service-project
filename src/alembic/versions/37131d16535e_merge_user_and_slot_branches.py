"""merge user and slot branches

Revision ID: 37131d16535e
Revises: 90f5e5f17929, e48df7117ad1
Create Date: 2025-12-16 02:07:08.300674

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37131d16535e'
down_revision: Union[str, None] = ('90f5e5f17929', 'e48df7117ad1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
