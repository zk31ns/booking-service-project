import io
import os
import uuid
from pathlib import Path

from PIL import Image
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.constants import ErrorCode, Limits
from src.app.core.exceptions import (
    InternalServerException,
    ValidationException,
)
from src.app.models.media import Media


class MediaService:
    """Сервис для загрузки и обработки медиа-файлов."""

    MEDIA_DIR = Path('media')
    ALLOWED_MIMETYPES = Limits.ALLOWED_IMAGE_MIMETYPES
    MAX_SIZE_BYTES = Limits.MAX_UPLOAD_SIZE_BYTES

    @classmethod
    async def upload(
            cls,
            session: AsyncSession,
            file_bytes: bytes,
            content_type: str,
    ) -> Media:
        """Загрузить и сохранить файл."""
        if content_type not in cls.ALLOWED_MIMETYPES:
            logger.error(f'Недопустимый тип файла: получен={content_type}, '
                         f'разрешены={cls.ALLOWED_MIMETYPES}')
            raise ValidationException(
                ErrorCode.INVALID_FILE_TYPE,
                detail='Недопустимый тип файла (разрешены JPG, PNG)'
        )

        file_size_mb = len(file_bytes) / (1024 * 1024)
        if len(file_bytes) > cls.MAX_SIZE_BYTES:
            logger.warning(
                f'Файл слишком большой: '
                f'размер={file_size_mb:.2f}MB, '
                f'макс={cls.MAX_SIZE_BYTES / (1024 * 1024)}MB'
            )
            raise ValidationException(
                ErrorCode.FILE_TOO_LARGE,
                detail='Файл слишком большой (макс. 5MB)'

            )
        logger.info(f'Начало обработки изображения: размер='
                    f'{file_size_mb:.2f}MB')
        try:

            image = Image.open(io.BytesIO(file_bytes))
            original_mode = image.mode

            if image.mode in ('RGBA', 'LA', 'P'):
                logger.info(f'Конвертация изображения из режима '
                            f'{original_mode} в RGB')
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1])
                image = background

            cls.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
            file_id = uuid.uuid4()
            file_path = cls.MEDIA_DIR / f'{file_id}.jpg'

            image.save(file_path, format='JPEG', quality=85, optimize=True)
            file_size = os.path.getsize(file_path)
            logger.info(
                f'Изображение успешно сохранено: '
                f'id={file_id}, путь={file_path}, размер={file_size} байт'
            )

        except (IOError, OSError) as e:
            logger.error(f'Ошибка сохранения файла: {str(e)}')
            raise InternalServerException(
                detail=f'Ошибка сохранения файла: {str(e)}'
            )

        except Exception as e:
            logger.error(f'Ошибка обработки изображения: {str(e)}')
            raise InternalServerException(
                detail=f'Ошибка обработки изображения: {str(e)}'
            )

        media = Media(
            id=file_id,
            file_path=str(file_path),
            mime_type='image/jpeg',
            file_size=file_size,
        )

        session.add(media)
        await session.flush()
        logger.info(f'Запись медиа создана в БД: id={file_id}')

        return media
