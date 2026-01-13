"""Add role column to users.

Revision ID: 5f3a2b1c9c4d
Revises: c8f1a9e3b7d2
Create Date: 2026-01-13 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5f3a2b1c9c4d'
down_revision = 'c8f1a9e3b7d2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('role', sa.Integer(), nullable=False, server_default='0'),
    )
    op.execute("UPDATE users SET role = 2 WHERE is_superuser IS TRUE")
    op.execute(
        "UPDATE users SET role = 1 "
        "WHERE role = 0 AND EXISTS ("
        "SELECT 1 FROM cafe_managers cm WHERE cm.user_id = users.id)"
    )


def downgrade() -> None:
    op.drop_column('users', 'role')
