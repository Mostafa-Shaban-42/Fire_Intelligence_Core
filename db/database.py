import os
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from db.base import Base

logger = logging.getLogger("fire_intelligence.db")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/fire_intelligence_db",
)

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DB_ECHO", "False").lower() in ("true", "1"),
    pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
    pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
    pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "1800")),
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as exc:
            await session.rollback()
            logger.error(f"Database session transaction failed: {exc}")
            raise
        finally:
            await session.close()


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)