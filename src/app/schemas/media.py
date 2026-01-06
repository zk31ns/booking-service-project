from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.base import TimestampedSchema


class MediaResponse(BaseModel):
    """Схема ответа при загрузке файла.

    Содержит информацию о загруженном медиа-файле.
    """

    id: UUID = Field(..., description='Уникальный идентификатор файла')
    file_path: str = Field(..., description='Путь к файлу на сервере')
    mime_type: str = Field(..., description='MIME тип файла')
    file_size: int = Field(..., description='Размер файла в байтах')

    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore',
        json_schema_extra={
            'example': {
                'id': '550e8400-e29b-41d4-a716-446655440000',
                'file_path': 'media/550e8400-e29b-41d4-a716-446655440000.jpg',
                'mime_type': 'image/jpeg',
                'file_size': 102400,
            }
        },
    )


class MediaInfo(TimestampedSchema):
    """Схема информации о медиа-файле.

    Используется для получения информации об уже загруженном файле.
    """

    id: UUID = Field(..., description='Уникальный идентификатор файла')
    mime_type: str = Field(..., description='MIME тип файла')
    file_size: int = Field(..., description='Размер файла в байтах')

    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore',
        json_schema_extra={
            'example': {
                'id': '550e8400-e29b-41d4-a716-446655440000',
                'mime_type': 'image/jpeg',
                'file_size': 102400,
                'created_at': '2025-12-21T00:07:00Z',
            }
        },
    )
