from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MediaResponse(BaseModel):
    """Ответ при загрузке файла."""

    id: UUID = Field(..., description='Уникальный идентификатор файла')
    file_path: str = Field(..., description='Путь к файлу на сервере')
    mime_type: str = Field(..., description='MIME тип файла')
    file_size: int = Field(..., description='Размер файла в байтах')

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            'example': {
                'id': '550e8400-e29b-41d4-a716-446655440000',
                'file_path': 'media/550e8400-e29b-41d4-a716-446655440000.jpg',
                'mime_type': 'image/jpeg',
                'file_size': 102400,
            }
        },
    )


class MediaInfo(BaseModel):
    """Информация о файле."""

    id: UUID = Field(..., description='Уникальный идентификатор файла')
    mime_type: str = Field(..., description='MIME тип файла')
    file_size: int = Field(..., description='Размер файла в байтах')
    created_at: datetime = Field(..., description='Дата создания')

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            'example': {
                'id': '550e8400-e29b-41d4-a716-446655440000',
                'mime_type': 'image/jpeg',
                'file_size': 102400,
                'created_at': '2025-12-21T00:07:00Z',
            }
        },
    )
