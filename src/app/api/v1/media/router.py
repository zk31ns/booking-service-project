from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.api.v1.media.schemas import MediaInfo, MediaResponse
from src.app.api.v1.media.service import MediaService
from src.app.core.constants import ErrorCode
from src.app.core.exceptions import NotFoundException
from src.app.db.session import get_session
from src.app.models.media import Media

# from src.app.api.v1.users.dependencies import get_current_user, get_db
# from src.app.models import User


router = APIRouter(prefix='/media')


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    response_model=MediaResponse,
)
async def upload_media(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Загрузить медиа-файл."""
    # TODO: Добавить проверку прав доступа (только Admin/Manager)
    # TODO: from src.app.api.v1.users.dependencies import get_current_user
    # TODO: if current_user.role not in ["admin", "manager"]:
    # TODO:    raise AuthorizationException(ErrorCode.INSUFFICIENT_PERMISSIONS)

    file_bytes = await file.read()

    media = await MediaService.upload(
        session=session,
        file_bytes=file_bytes,
        content_type=file.content_type or 'application/octet-stream',
    )

    await session.commit()
    return media


@router.get("/{media_id}", response_model=MediaInfo)
async def get_media_info(
    media_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Получить информацию о медиа-файле."""
    result = await session.execute(
        select(Media).where(Media.id == media_id, Media.active)
    )
    media = result.scalar_one_or_none()

    if not media:
        raise NotFoundException(
            ErrorCode.MEDIA_NOT_FOUND,
            detail='Изображение не найдено'
        )

    return media


@router.get("/{media_id}/file")
async def download_media(
    media_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Скачать медиа-файл."""
    result = await session.execute(
        select(Media).where(Media.id == media_id, Media.active)
    )
    media = result.scalar_one_or_none()

    if not media:
        raise NotFoundException(
            ErrorCode.MEDIA_NOT_FOUND,
            detail='Изображение не найдено'
        )

    return FileResponse(media.file_path, media_type=media.mime_type)


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(
    media_id: UUID,
    session: AsyncSession = Depends(get_session)
) -> None:
    """Удалить медиа-файл."""
    # TODO: Добавить проверку прав доступа (только Admin/Manager)
    # TODO: from src.app.api.v1.users.dependencies import get_current_user
    # TODO: if current_user.role not in ["admin", "manager"]:
    # TODO:    raise AuthorizationException(ErrorCode.INSUFFICIENT_PERMISSIONS)

    result = await session.execute(
        select(Media).where(Media.id == media_id, Media.active)
    )
    media = result.scalar_one_or_none()

    if not media:
        raise NotFoundException(
            ErrorCode.MEDIA_NOT_FOUND,
            detail='Изображение не найдено'
        )

    media.active = False
    await session.commit()
