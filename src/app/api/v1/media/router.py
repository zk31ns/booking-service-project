from uuid import UUID

from fastapi import APIRouter, Depends, File, Path, UploadFile, status
from fastapi.responses import FileResponse
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.media.schemas import MediaInfo, MediaResponse
from app.api.v1.media.service import MediaService
from app.api.v1.users.dependencies import get_current_user
from app.core.constants import ErrorCode
from app.core.exceptions import AuthorizationException, NotFoundException
from app.db.session import get_session
from app.models import User
from app.models.media import Media

router = APIRouter(prefix='/media')


@router.post(
    '/upload',
    status_code=status.HTTP_200_OK,
    response_model=MediaResponse,
)
async def upload_media(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> MediaResponse:
    """Загрузить медиа-файл."""
    if current_user.role not in ['admin', 'manager']:
        raise AuthorizationException(ErrorCode.INSUFFICIENT_PERMISSIONS)

    logger.info(
        f'Начало загрузки файла: {file.filename}, тип: {file.content_type}'
    )

    file_bytes = await file.read()

    media = await MediaService.upload(
        session=session,
        file_bytes=file_bytes,
        content_type=file.content_type or 'application/octet-stream',
    )

    await session.commit()
    logger.info(
        f'Файл успешно загружен: id={media.id}, размер={media.file_size} байт'
    )
    return media


@router.get('/{media_id}', response_model=MediaInfo)
async def get_media_info(
    media_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> MediaInfo:
    """Получить информацию о медиа-файле."""
    logger.info(f'Запрос информации о медиа: id={media_id}')
    result = await session.execute(
        select(Media).where(Media.id == media_id, Media.active)
    )
    media = result.scalar_one_or_none()

    if not media:
        logger.warning(f'Медиа не найдено: id={media_id}')
        raise NotFoundException(
            ErrorCode.MEDIA_NOT_FOUND, detail='Изображение не найдено'
        )

    logger.info(f'Информация о медиа получена: id={media_id}')
    return media


@router.get('/{media_id}/file')
async def download_media(
    media_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    """Скачать медиа-файл."""
    logger.info(f'Запрос на скачивание медиа: id={media_id}')
    result = await session.execute(
        select(Media).where(Media.id == media_id, Media.active)
    )
    media = result.scalar_one_or_none()

    if not media:
        logger.warning(f'Медиа для скачивания не найдено: id={media_id}')
        raise NotFoundException(
            ErrorCode.MEDIA_NOT_FOUND, detail='Изображение не найдено'
        )

    logger.info(
        f'Медиа успешно отправлено: id={media_id}, путь={media.file_path}'
    )
    return FileResponse(media.file_path, media_type=media.mime_type)


@router.delete('/{media_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(
    media_id: UUID = Path(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """Удалить медиа-файл."""
    if current_user.role not in ['admin', 'manager']:
        raise AuthorizationException(ErrorCode.INSUFFICIENT_PERMISSIONS)

    logger.info(f'Запрос на удаление медиа: id={media_id}')
    result = await session.execute(
        select(Media).where(Media.id == media_id, Media.active)
    )
    media = result.scalar_one_or_none()

    if not media:
        logger.warning(f'Медиа для удаления не найдено: id={media_id}')
        raise NotFoundException(
            ErrorCode.MEDIA_NOT_FOUND, detail='Изображение не найдено'
        )

    media.active = False
    await session.commit()
    logger.info(f'Медиа успешно удалено: id={media_id}')
