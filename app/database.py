"""
Database Configuration & Session Management Module.

Uses SQLAlchemy 2.0 with the asynchronous SQLite driver (aiosqlite).
Provides asynchronous session management, connection pooling, and
automatic lifecycle management for route handlers and background tasks.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings
from app.logging_config import logger

settings = get_settings()

# Asynchronous SQLAlchemy Engine
# SQLite requires connect_args={"check_same_thread": False} when used concurrently
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=connect_args,
    future=True,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(AsyncAttrs, DeclarativeBase):
    """
    Base declarative class for all SQLAlchemy ORM models.
    Inherits AsyncAttrs for lazy loading compatibility in async contexts.
    """
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an asynchronous database session.
    Automatically commits valid transactions, rolls back upon unhandled
    exceptions, and closes the session upon request completion.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as exc:
            await session.rollback()
            logger.error(f"Database transaction rollback due to: {exc}")
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initializes database tables if they do not already exist.
    Called during application lifespan startup.
    """
    # Import models here so Base knows about all registered tables
    from app import models  # noqa: F401

    logger.info("Initializing database schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema initialized successfully.")


async def close_db() -> None:
    """
    Gracefully disposes the database engine pool on application shutdown.
    """
    logger.info("Closing database engine connections...")
    await engine.dispose()
    logger.info("Database engine connections closed.")
