"""Initialize test data in the database."""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.users import User


async def init_test_data() -> None:
    """Create test users for testing."""
    # Create async engine
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        future=True,
    )

    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Check if test user already exists
        from sqlalchemy import select

        result = await session.execute(
            select(User).where(User.email == 'test@example.com')
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print('Test user already exists')
            return

        # Create test users
        users = [
            User(
                username='testuser1',
                email='test@example.com',
                phone='+79999999999',
                password_hash=get_password_hash('testpass123'),
                is_blocked=False,
                is_superuser=False,
            ),
            User(
                username='manager1',
                email='manager@example.com',
                phone='+79999999998',
                password_hash=get_password_hash('managerpass123'),
                is_blocked=False,
                is_superuser=False,
            ),
            User(
                username='admin',
                email='admin@example.com',
                phone='+79999999997',
                password_hash=get_password_hash('adminpass123'),
                is_blocked=False,
                is_superuser=True,
            ),
        ]

        for user in users:
            session.add(user)

        await session.commit()
        print(f'Created {len(users)} test users')


if __name__ == '__main__':
    asyncio.run(init_test_data())
