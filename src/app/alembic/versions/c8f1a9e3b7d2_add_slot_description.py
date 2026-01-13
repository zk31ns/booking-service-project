"""Add description column to slots.

Revision ID: c8f1a9e3b7d2
Revises: b7d9f2a3c1e0
Create Date: 2026-01-13 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c8f1a9e3b7d2'
down_revision = 'b7d9f2a3c1e0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'slots',
        sa.Column('description', sa.String(length=1000), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('slots', 'description')
