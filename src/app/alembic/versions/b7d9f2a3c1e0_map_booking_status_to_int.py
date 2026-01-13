"""map booking status to int enum.

Revision ID: b7d9f2a3c1e0
Revises: f5f10f45425e
Create Date: 2026-01-12
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = 'b7d9f2a3c1e0'
down_revision = 'f5f10f45425e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Map string booking statuses to ints and alter column type."""
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'bookings'
                  AND column_name = 'status'
                  AND data_type <> 'integer'
            ) THEN
                UPDATE bookings
                SET status = CASE
                    WHEN status IN ('PENDING', 'pending', 'CONFIRMED', 'confirmed')
                        THEN '0'
                    WHEN status IN (
                        'CANCELLED',
                        'cancelled',
                        'CANCELED',
                        'canceled',
                        'COMPLETED',
                        'completed'
                    ) THEN '1'
                    WHEN status IN ('ACTIVE', 'active')
                        THEN '2'
                    ELSE status
                END;

                ALTER TABLE bookings
                ALTER COLUMN status TYPE INTEGER
                USING status::integer;
            END IF;
        END$$;
        """
    )
    op.execute(
        """
        UPDATE bookings
        SET active = FALSE
        WHERE status = 1 AND active IS TRUE;
        """
    )


def downgrade() -> None:
    """Revert booking status column to string values."""
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'bookings'
                  AND column_name = 'status'
                  AND data_type = 'integer'
            ) THEN
                ALTER TABLE bookings
                ALTER COLUMN status TYPE VARCHAR
                USING status::text;

                UPDATE bookings
                SET status = CASE
                    WHEN status = '0' THEN 'PENDING'
                    WHEN status = '1' THEN 'CANCELLED'
                    WHEN status = '2' THEN 'CONFIRMED'
                    ELSE status
                END;
            END IF;
        END$$;
        """
    )
