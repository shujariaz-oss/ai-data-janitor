"""Database engine and session management."""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

settings = get_settings()

raw_url = str(settings.database_url)
async_url = raw_url.replace("postgresql://", "postgresql+asyncpg://")
if "postgresql+asyncpg" not in async_url:
    async_url = async_url.replace("postgres://", "postgresql+asyncpg://")

engine = create_async_engine(
    async_url,
    echo=settings.debug,
    future=True,
    pool_size=20,
    max_overflow=10,
)

AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
