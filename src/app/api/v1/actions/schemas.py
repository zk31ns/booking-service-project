from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import Limits


class ActionBase(BaseModel):
    """Базовая схема акции."""

    name: str = Field(
        ...,
        min_length=Limits.ACTION_NAME_MIN_LENGTH,
        max_length=Limits.ACTION_NAME_MAX_LENGTH,
    )
    description: str | None = Field(
        None, max_length=Limits.ACTION_DESCRIPTION_MAX_LENGTH
    )
    photo_id: str | None = Field(None)


class ActionCreate(ActionBase):
    """Схема для создания акции."""

    pass


class ActionUpdate(BaseModel):
    """Схема для обновления акции."""

    name: str | None = Field(
        None,
        min_length=Limits.ACTION_NAME_MIN_LENGTH,
        max_length=Limits.ACTION_NAME_MAX_LENGTH,
    )
    description: str | None = Field(
        None, max_length=Limits.ACTION_DESCRIPTION_MAX_LENGTH
    )
    photo_id: str | None = Field(None)


class ActionInfo(ActionBase):
    """Схема акции для получения информации."""

    id: int
    active: bool

    model_config = ConfigDict(from_attributes=True)
