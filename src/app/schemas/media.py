from uuid import UUID

from pydantic import ConfigDict, Field

from app.schemas.base import BaseResponse


class MediaInfo(BaseResponse):
    """Media metadata for upload responses (TZ-aligned)."""

    media_id: UUID = Field(
        ..., alias='id', description='Media object identifier'
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
