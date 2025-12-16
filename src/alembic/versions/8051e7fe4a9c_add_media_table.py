"""add media table

Revision ID: 8051e7fe4a9c
Revises: 90f5e5f17929
Create Date: 2025-12-16 13:38:42.192037

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '8051e7fe4a9c'
down_revision: Union[str, None] = '90f5e5f17929'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'media',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('mime_type', sa.String(length=50), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_path')
    )

    op.create_index('ix_media_file_path', 'media', ['file_path'])
    op.create_index('ix_media_created_at', 'media', ['created_at'])
    op.create_index('ix_media_active', 'media', ['active'])


def downgrade() -> None:
    op.drop_index('ix_media_active', table_name='media')
    op.drop_index('ix_media_created_at', table_name='media')
    op.drop_index('ix_media_file_path', table_name='media')
    op.drop_table('media')