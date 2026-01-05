from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.constants import Limits
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.cafes import Cafe


class Table(Base):
    """Модель столика в кафе."""

    __tablename__ = 'tables'
    __table_args__ = (Index('ix_tables_id', 'id'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    cafe_id: Mapped[int] = mapped_column(
        ForeignKey('cafes.id', ondelete='CASCADE'),
        nullable=False,
    )
    seats: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(
        String(Limits.MAX_DESCRIPTION_LENGTH),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    active: Mapped[bool] = mapped_column(default=True, nullable=False)
    cafe: Mapped['Cafe'] = relationship('Cafe', back_populates='tables')

    def __repr__(self) -> str:
        return (
            f'<Table(id={self.id},cafe_id={self.cafe_id},seats={self.seats})>'
        )
