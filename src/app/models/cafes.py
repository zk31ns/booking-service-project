from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.constants import Limits
from app.db.base import Base
from app.models.tables import Table

if TYPE_CHECKING:
    from app.models.media import Media


class Cafe(Base):
    """Модель кафе/ресторана."""

    __tablename__ = 'cafes'
    __table_args__ = (
        Index('idx_cafe_active', 'active'),
        Index('idx_cafe_name', 'name'),
        Index('idx_cafe_address', 'address'),
        Index('idx_cafe_phone', 'phone'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(Limits.MAX_CAFE_NAME_LENGTH),
        unique=True,
        nullable=False,
    )
    address: Mapped[str] = mapped_column(
        String(Limits.MAX_DESCRIPTION_LENGTH),
        nullable=False,
    )
    phone: Mapped[str] = mapped_column(
        String(Limits.MAX_PHONE_LENGTH),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    photo_id: Mapped[UUID | None] = mapped_column(
        ForeignKey('media.id', ondelete='SET NULL'),
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
    active: Mapped[bool] = mapped_column(default=True)
    tables: Mapped[list['Table']] = relationship(
        'Table',
        back_populates='cafe',
        cascade='all, delete-orphan',
    )

    photo: Mapped['Media | None'] = relationship(
        'Media',
        foreign_keys=[photo_id],
        back_populates='cafe_photos',
    )

    def __repr__(self) -> str:
        return f'<Cafe(id="{self.id}", name="{self.name}")>'
