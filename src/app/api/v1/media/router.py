from pathlib import Path as FsPath
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import FileResponse
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_manager_or_superuser
from app.core.constants import API, ErrorCode, Messages
from app.core.database import get_session
from app.core.exceptions import NotFoundException
from app.models import User
from app.models.media import Media
from app.schemas.media import MediaInfo
from app.services.media import MediaService

router = APIRouter(prefix='/media', tags=API.MEDIA)


@router.get(
    '/{media_id}',
    response_class=FileResponse,
    summary='Возвращает изображение в бинарном формате',
    responses={
        200: {
            'content': {
                'image/jpeg': {
                    'schema': {'type': 'string', 'format': 'binary'}
                },
                'image/png': {
                    'schema': {'type': 'string', 'format': 'binary'}
                },
            },
            'description': (
                'Успешно. Возвращает изображение в бинарном формате'
            ),
        }
    },
)
async def get_media_file(
    media_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    """Скачать медиафайл по идентификатору.

    Args:
        media_id: Идентификатор медиафайла.
        session: Асинхронная сессия БД.

    Returns:
        FileResponse: Файл медиа.

    Raises:
        NotFoundException: Если запись или файл не найдены.

    """
    logger.info(f'Request media file: id={media_id}')
    result = await session.execute(
        select(Media).where(Media.id == media_id, Media.active)
    )
    media = result.scalar_one_or_none()

    if not media:
        logger.warning(f'Media not found: id={media_id}')
        raise NotFoundException(
            ErrorCode.MEDIA_NOT_FOUND,
            detail=Messages.errors[ErrorCode.MEDIA_NOT_FOUND],
        )

    file_path = FsPath(media.file_path)
    if not file_path.exists():
        logger.warning(f'Media file missing: id={media_id}')
        raise NotFoundException(
            ErrorCode.MEDIA_NOT_FOUND,
            detail=Messages.errors[ErrorCode.MEDIA_NOT_FOUND],
        )

    return FileResponse(str(file_path), media_type=media.mime_type)


@router.post(
    '',
    status_code=status.HTTP_200_OK,
    response_model=MediaInfo,
    summary='Загрузка изображения',
    description=(
        'Загрузка изображения на сервер. Поддерживаются форматы jpg, png. '
        'Размер файла не более 5Мб. Только для администраторов и менеджеров'
    ),
)
async def upload_media(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    _current_user: User = Depends(get_current_manager_or_superuser),
) -> MediaInfo:
    """Загрузить медиафайл.

    Файл сохраняется на диск и фиксируется в базе.

    Args:
        file: Загружаемый файл.
        session: Асинхронная сессия БД.
        _current_user: Текущий пользователь с правами менеджера/админа.

    Returns:
        MediaInfo: Информация о загруженном медиафайле.

    """
    logger.info(
        f'Upload media: name={file.filename}, content_type={file.content_type}'
    )

    file_bytes = await file.read()
    media = await MediaService.upload(
        session=session,
        file_bytes=file_bytes,
        content_type=file.content_type or 'application/octet-stream',
    )

    await session.commit()
    logger.info(f'Media uploaded: id={media.id}')
    return MediaInfo.model_validate(media)
