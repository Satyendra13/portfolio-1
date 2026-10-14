from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from backend.app.core.config import settings
from backend.app.db.base import Base

# Async Engine for FastAPI async requests
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Sync Engine for Alembic migrations or sync operations
sync_engine = create_engine(
    settings.DATABASE_URL_SYNC,
    echo=False,
    future=True,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    # If postgres, enable pgvector extension if not exists
    if "postgres" in settings.DATABASE_URL:
        async with async_engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    
    # Import all models so Base has metadata registered
    import backend.app.models  # noqa
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
