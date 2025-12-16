"""Роутер для работы с медиа-файлами."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.media import Media
from src.app.api.v1.media.schemas import MediaInfo, MediaResponse
from src.app.api.v1.media.service import MediaService
from src.app.db.session import get_session
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
    # current_user: User = Depends(get_current_user),
):
    """Загрузить медиа-файл."""
    # if current_user.role not in ["admin", "manager"]:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Недостаточно прав",
    #     )

    file_bytes = await file.read()

    media = await MediaService.upload(
        session=session,
        file_bytes=file_bytes,
        content_type=file.content_type or "application/octet-stream",
    )

    await session.commit()

    return media


@router.get("/{media_id}", response_model=MediaInfo)
async def get_media_info(
    media_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Получить информацию о медиа-файле."""
    result = await session.execute(
        select(Media).where(Media.id == media_id, Media.active == True)
    )
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файл не найден",
        )

    return media


@router.get("/{media_id}/file")
async def download_media(
    media_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Скачать медиа-файл."""
    result = await session.execute(
        select(Media).where(Media.id == media_id, Media.active == True)
    )
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файл не найден",
        )

    return FileResponse(media.file_path, media_type=media.mime_type)


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(
    media_id: UUID,
    session: AsyncSession = Depends(get_session),
    # current_user: User = Depends(get_current_user),
):
    """Удалить медиа-файл."""
    # if current_user.role not in ["admin", "manager"]:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Недостаточно прав",
    #     )

    result = await session.execute(select(Media).where(Media.id == media_id))
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файл не найден",
        )

    media.active = False
    await session.commit()
