import io
import os
import uuid
from pathlib import Path

from PIL import Image
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.core.constants import ErrorCode, Limits
from src.app.core.exceptions import (
    InternalServerException,
    ValidationException,
)
from src.app.models.media import Media


class MediaService:
    """Сервис для загрузки и обработки медиа-файлов."""

    MEDIA_DIR = Path(settings.media_path)
    ALLOWED_MIMETYPES = Limits.ALLOWED_IMAGE_MIMETYPES
    MAX_SIZE_BYTES = Limits.MAX_UPLOAD_SIZE_BYTES

    @classmethod
    def _validate_file(cls, file_bytes: bytes, content_type: str) -> None:
        """Валидация типа и размера файла."""
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
        logger.info(f'Начало обработки изображения: '
                    f'размер={file_size_mb:.2f}MB')

    @classmethod
    def _validate_image_dimensions(cls, image: Image.Image) -> None:
        """Валидация размеров изображения."""
        if (image.width < Limits.MIN_IMAGE_WIDTH
                or image.height < Limits.MIN_IMAGE_HEIGHT):
            logger.warning(
                f'Изображение слишком маленькое: '
                f'{image.width}x{image.height}px, минимум: '
                f'{Limits.MIN_IMAGE_WIDTH}x{Limits.MIN_IMAGE_HEIGHT}px'
            )
            raise ValidationException(
                ErrorCode.IMAGE_TOO_SMALL,
                detail=f'Изображение слишком маленькое. '
                       f'Минимальный размер: {Limits.MIN_IMAGE_WIDTH}'
                       f'x{Limits.MIN_IMAGE_HEIGHT}px'
            )

        if (image.width > Limits.MAX_IMAGE_WIDTH
                or image.height > Limits.MAX_IMAGE_HEIGHT):
            logger.warning(
                f'Изображение слишком большое: '
                f'{image.width}x{image.height}px, '
                f'максимум: {Limits.MAX_IMAGE_WIDTH}'
                f'x{Limits.MAX_IMAGE_HEIGHT}px'
            )
            raise ValidationException(
                ErrorCode.IMAGE_TOO_LARGE_DIMENSIONS,
                detail=f'Изображение слишком большое. '
                       f'Максимальный размер: {Limits.MAX_IMAGE_WIDTH}'
                       f'x{Limits.MAX_IMAGE_HEIGHT}px'
            )
        logger.info(f'Размеры изображения валидны: '
                    f'{image.width}x{image.height}px')

    @classmethod
    def _process_and_save_image(
            cls, image: Image.Image, file_id: uuid.UUID
    ) -> tuple[Path, int]:
        """Обработка и сохранение изображения."""
        try:
            original_mode = image.mode

            if image.mode in ('RGBA', 'LA', 'P'):
                logger.info(f'Конвертация изображения '
                            f'из режима {original_mode} в RGB')
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1])
                image = background

            cls.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
            file_path = cls.MEDIA_DIR / f'{file_id}.jpg'

            image.save(file_path, format='JPEG', quality=85, optimize=True)
            file_size = os.path.getsize(file_path)

            logger.info(
                f'Изображение успешно сохранено: '
                f'id={file_id}, путь={file_path}, размер={file_size} байт'
            )
            return file_path, file_size

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

    @classmethod
    async def upload(
            cls,
            session: AsyncSession,
            file_bytes: bytes,
            content_type: str,
    ) -> Media:
        """Загрузить и сохранить файл."""
        cls._validate_file(file_bytes, content_type)

        try:
            image = Image.open(io.BytesIO(file_bytes))
        except Exception as e:
            logger.error(f'Ошибка открытия изображения: {str(e)}')
            raise ValidationException(
                ErrorCode.INVALID_FILE_TYPE,
                detail='Не удалось открыть изображение'
            )

        cls._validate_image_dimensions(image)

        file_id = uuid.uuid4()
        file_path, file_size = cls._process_and_save_image(image, file_id)

        media = Media(
            id=file_id,
            file_path=str(file_path),
            mime_type='image/jpeg',
            file_size=file_size,
        )

        try:
            session.add(media)
            await session.flush()
            logger.info(f'Запись медиа создана в БД: id={file_id}')
            return media
        except Exception as e:
            try:
                file_path.unlink()
                logger.warning(f'Файл удален после ошибки БД: {file_path}')
            except Exception as cleanup_error:
                logger.error(f'Ошибка удаления файла при откате: '
                             f'{cleanup_error}')
            logger.error(f'Ошибка при сохранении в БД: {str(e)}')
            raise
