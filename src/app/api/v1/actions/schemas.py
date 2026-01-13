from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.base import TimestampedSchema
from app.schemas.cafes import CafeShortInfo


class ActionCreate(BaseModel):
    """Схема создания акции.

    Attributes:
        cafes_id: Список идентификаторов кафе.
        description: Описание акции.
        photo_id: Идентификатор фото.

    """

    cafes_id: list[int] = Field(..., description='Список ID кафе.')
    description: str = Field(..., description='Описание акции.')
    photo_id: UUID = Field(..., description='ID фото.')


class ActionUpdate(BaseModel):
    """Схема обновления акции.

    Attributes:
        cafes_id: Список идентификаторов кафе.
        description: Описание акции.
        photo_id: Идентификатор фото.
        active: Признак активности.

    """

    cafes_id: list[int] | None = Field(None, description='Список ID кафе.')
    description: str | None = Field(None, description='Описание акции.')
    photo_id: UUID | None = Field(None, description='ID фото.')
    active: bool | None = Field(
        None,
        validation_alias='is_active',
        serialization_alias='is_active',
        description='Признак активности акции.',
    )

    model_config = ConfigDict(populate_by_name=True)


class ActionInfo(TimestampedSchema):
    """Схема ответа по акции.

    Attributes:
        cafes: Список кафе, связанных с акцией.
        description: Описание акции.
        photo_id: Идентификатор фото.
        active: Признак активности.

    """

    cafes: list[CafeShortInfo] = Field(
        default_factory=list,
        description='Список кафе для этой акции.',
    )
    description: str = Field(..., description='Описание акции.')
    photo_id: UUID = Field(..., description='ID фото.')
    active: bool = Field(
        ...,
        validation_alias='is_active',
        serialization_alias='is_active',
        description='Признак активности акции.',
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        extra='ignore',
    )
