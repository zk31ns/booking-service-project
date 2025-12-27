import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.db.base import Base

if TYPE_CHECKING:
    from app.models.cafes import Cafe


class Media(Base):
    """Модель для хранения метаданных загруженных файлов."""

    __tablename__ = 'media'

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    file_path: Mapped[str] = mapped_column(
        String(512), unique=True, nullable=False
    )
    mime_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    cafe_photos: Mapped[list['Cafe']] = relationship(
        'Cafe',
        foreign_keys='Cafe.photo_id',
        back_populates='photo',
    )

    __table_args__ = (
        Index('ix_media_file_path', 'file_path'),
        Index('ix_media_created_at', 'created_at'),
        Index('ix_media_active', 'active'),
    )
