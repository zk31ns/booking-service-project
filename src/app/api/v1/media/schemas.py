"""Pydantic схемы для медиа-файлов."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MediaResponse(BaseModel):
    """Ответ при загрузке файла."""

    id: UUID
    file_path: str
    mime_type: str
    file_size: int

    class Config:
        from_attributes = True


class MediaInfo(BaseModel):
    """Информация о файле."""

    id: UUID
    mime_type: str
    file_size: int
    created_at: datetime

    class Config:
        from_attributes = True
