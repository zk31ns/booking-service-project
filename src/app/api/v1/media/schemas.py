from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MediaResponse(BaseModel):
    """Ответ при загрузке файла."""

    id: UUID
    file_path: str
    mime_type: str
    file_size: int

    model_config = ConfigDict(from_attributes=True)


class MediaInfo(BaseModel):
    """Информация о файле."""

    id: UUID
    mime_type: str
    file_size: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
