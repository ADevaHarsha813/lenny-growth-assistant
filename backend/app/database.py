"""Async SQLAlchemy database setup."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.config import settings
import structlog

log = structlog.get_logger()

class Base(DeclarativeBase):
    pass


_engine = None
async_session_maker = None


def get_engine():
    global _engine, async_session_maker
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_size=5,
            max_overflow=10,
        )
        async_session_maker = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _engine


async def get_db():
    """FastAPI dependency for DB sessions."""
    get_engine()  # ensure initialized
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    """Create all tables on startup."""
    engine = get_engine()
    from app.models.db import Session, Message, Artifact  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("tables_created")
