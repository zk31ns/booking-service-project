"""prepare booking_date change

Revision ID: 8fbb11e2f082
Revises: f35a577907a1
Create Date: 2025-12-21 00:43:58.721915

"""

import sqlalchemy as sa
from alembic import op

revision = '8fbb11e2f082'
down_revision = 'f35a577907a1'


def upgrade():
    op.add_column(
        'bookings', sa.Column('booking_date_new', sa.Date(), nullable=True)
    )

    op.execute("""
        UPDATE bookings 
        SET booking_date_new = booking_date::date
    """)

    op.drop_column('bookings', 'booking_date')

    op.alter_column(
        'bookings', 'booking_date_new', new_column_name='booking_date'
    )

    op.alter_column('bookings', 'booking_date', nullable=False)


def downgrade():
    op.add_column(
        'bookings', sa.Column('booking_date_old', sa.DateTime(), nullable=True)
    )
    op.execute("""
        UPDATE bookings 
        SET booking_date_old = booking_date
    """)
    op.drop_column('bookings', 'booking_date')
    op.alter_column(
        'bookings', 'booking_date_old', new_column_name='booking_date'
    )
    op.alter_column('bookings', 'booking_date', nullable=False)
