import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from apps.api.app.core.config import settings

# Determine engine URL
database_url = settings.DATABASE_URL
if database_url.startswith("sqlite"):
    # Ensure relative sqlite path resolves properly
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

engine = create_async_engine(
    database_url,
    echo=False,
    connect_args=connect_args,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
