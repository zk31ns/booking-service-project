"""feat: add cafes and tables with timestamps.

Revision ID: 0384266657a9
Revises: 0384266657a8
Create Date: 2025-12-21 16:10:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0384266657a9'
down_revision: Union[str, None] = '0384266657a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create cafes and tables schema."""
    # Create cafes table
    op.create_table(
        'cafes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('address', sa.String(500), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('email', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('logo_id', sa.String(100), nullable=True),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('opening_time', sa.Time(), nullable=True),
        sa.Column('closing_time', sa.Time(), nullable=True),
        sa.Column(
            'average_bill',
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        ),
        sa.Column(
            'active',
            sa.Boolean(),
            nullable=False,
            server_default='true',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.Index('idx_cafe_active', 'active'),
        sa.Index('idx_cafe_name', 'name'),
        sa.Index('idx_cafe_address', 'address'),
        sa.Index('idx_cafe_phone', 'phone'),
    )

    # Create tables table
    op.create_table(
        'tables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cafe_id', sa.Integer(), nullable=False),
        sa.Column('table_number', sa.Integer(), nullable=False),
        sa.Column('seat_count', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column(
            'is_smoking_area',
            sa.Boolean(),
            nullable=False,
            server_default='false',
        ),
        sa.Column(
            'has_power_outlet',
            sa.Boolean(),
            nullable=False,
            server_default='false',
        ),
        sa.Column(
            'has_window',
            sa.Boolean(),
            nullable=False,
            server_default='false',
        ),
        sa.Column(
            'active',
            sa.Boolean(),
            nullable=False,
            server_default='true',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['cafe_id'], ['cafes.id']),
        sa.UniqueConstraint('cafe_id', 'table_number'),
        sa.Index('idx_table_cafe_id', 'cafe_id'),
        sa.Index('idx_table_active', 'active'),
    )


def downgrade() -> None:
    """Drop cafes and tables schema."""
    op.drop_table('tables')
    op.drop_table('cafes')
