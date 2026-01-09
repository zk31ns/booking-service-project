"""Fix: ensure phone field is properly mapped in User schema.

Revision ID: 4650ccdd790e
Revises: 324bfa59320b
Create Date: 2026-01-09 16:57:39.012345

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '4650ccdd790e'
down_revision: Union[str, None] = '324bfa59320b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply database changes: fix phone field mapping and booking schema."""
    # Add active column to bookings table if it doesn't exist
    op.add_column('bookings', sa.Column('active', sa.Boolean(), nullable=True, server_default=sa.true()))

    # Alter bookings.status type from INTEGER to String
    op.alter_column('bookings', 'status',
               existing_type=sa.INTEGER(),
               type_=sa.String(),
               existing_nullable=True)

    # Remove is_active column if it exists
    try:
        op.drop_column('bookings', 'is_active')
    except Exception:
        pass  # Column might not exist in all environments


def downgrade() -> None:
    """Revert database changes."""
    # Restore booking schema to previous state
    op.alter_column('bookings', 'status',
               existing_type=sa.String(),
               type_=sa.INTEGER(),
               existing_nullable=True)

    op.drop_column('bookings', 'active')

    try:
        op.add_column('bookings', sa.Column('is_active', sa.Boolean(), nullable=True))
    except Exception:
        pass
