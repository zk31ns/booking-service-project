"""remove_slot_constraints_add_index

Revision ID: 50525fa22669
Revises: 37131d16535e
Create Date: 2025-12-16 02:07:21.065002

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '50525fa22669'
down_revision: Union[str, None] = '37131d16535e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('uq_cafe_slots', 'slots', type_='unique')
    op.drop_constraint('ck_slot_time_order', 'slots', type_='check')

    op.create_index(
        op.f('ix_slots_cafe_id'),
        'slots',
        ['cafe_id'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_slots_cafe_id'), table_name='slots')

    op.create_unique_constraint(
        'uq_cafe_slots',
        'slots',
        ['cafe_id', 'start_time', 'end_time']
    )

    op.create_check_constraint(
        'ck_slot_time_order',
        'slots',
        'start_time < end_time'
    )
