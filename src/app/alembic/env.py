"""Alembic environment for async SQLAlchemy migrations."""

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path
from typing import Any

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# Добавить корневую папку в путь для импорта (исправляет проблему с
# абсолютными импортами).
# В Docker: env.py находится в /app/app/alembic/, нужно добавить /app
# В локальной разработке: env.py находится в src/app/alembic/,
# нужно добавить корень проекта
# Используем более надежный способ - поднимаемся до директории,
# где находится app/
app_dir = Path(__file__).resolve().parent.parent  # /app/app или src/app
root_dir = app_dir.parent  # /app или src
sys.path.insert(0, str(root_dir))

from app.core.base import Base  # noqa: E402

# Import all models to register them with Base.metadata for autogenerate
from app.models import (  # noqa: F401, E402
    Action,
    Cafe,
    Dish,
    Table,
    User,
    cafe_managers,
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    import os

    # Use DATABASE_URL from environment if available, otherwise use alembic.ini
    url = os.getenv('DATABASE_URL') or config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Any) -> None:
    """Run migrations synchronously."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    import os
    from urllib.parse import quote_plus

    configuration = config.get_section(config.config_ini_section)
    # Prefer building DATABASE_URL from POSTGRES_* variables for Docker
    # (more reliable than parsing DATABASE_URL which may have encoding issues)
    postgres_user = os.getenv('POSTGRES_USER')
    postgres_password = os.getenv('POSTGRES_PASSWORD')
    postgres_db = os.getenv('POSTGRES_DB')
    postgres_host = os.getenv('POSTGRES_HOST')
    postgres_port = os.getenv('POSTGRES_PORT')

    if all([postgres_user, postgres_password, postgres_db, postgres_host]):
        # Build DATABASE_URL from individual variables (most reliable)
        # URL-encode password to handle special characters (e.g., dashes)
        encoded_password = quote_plus(postgres_password)
        database_url = (
            f'postgresql+asyncpg://{postgres_user}:{encoded_password}'
            f'@{postgres_host}:{postgres_port or "5432"}/{postgres_db}'
        )
    else:
        # Fallback to DATABASE_URL from environment or alembic.ini
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            database_url = config.get_main_option('sqlalchemy.url')

    configuration['sqlalchemy.url'] = database_url

    connectable = create_async_engine(
        configuration['sqlalchemy.url'],
        poolclass=pool.NullPool,
    )

    async with connectable.begin() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
