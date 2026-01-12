from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MediaInfo(BaseModel):
    """Схема ответа по медиафайлу.

    Attributes:
        media_id: Идентификатор медиафайла (UUID).

    """

    media_id: UUID = Field(
        ...,
        validation_alias='id',
        serialization_alias='media_id',
        description='ID медиафайла (UUID).',
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        extra='ignore',
        json_schema_extra={
            'example': {
                'media_id': '550e8400-e29b-41d4-a716-446655440000',
            }
        },
    )
