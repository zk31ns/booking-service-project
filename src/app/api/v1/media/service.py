import io
import os
import uuid
from pathlib import Path

from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media import Media
from app.core.constants import Limits


class MediaService:
    """Сервис для загрузки и обработки медиа-файлов."""

    MEDIA_DIR = Path('/app/media')
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
            raise ValueError(
                f'Недопустимый тип файла. '
                f'Разрешены: {", ".join(cls.ALLOWED_MIMETYPES)}'
            )

        if len(file_bytes) > cls.MAX_SIZE_BYTES:
            raise ValueError(
                f'Размер файла превышает максимум '
                f'({Limits.MAX_UPLOAD_SIZE_MB}МБ)'
            )

        image = Image.open(io.BytesIO(file_bytes))

        if image.mode in ('RGBA', 'LA', 'P'):
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

        media = Media(
            id=file_id,
            file_path=str(file_path),
            mime_type='image/jpeg',
            file_size=file_size,
        )

        session.add(media)
        await session.flush()

        return media
