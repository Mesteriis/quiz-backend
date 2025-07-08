"""
Database configuration and connection management.

This module sets up SQLAlchemy with declarative base and provides
database session management for the application.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import settings

# Create metadata with naming convention for better constraint names
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)


# Create declarative base for SQLAlchemy 2.0+
class Base(DeclarativeBase):
    """Base class for all database models."""

    metadata = metadata


# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    future=True,
    connect_args={"check_same_thread": False}
    if "sqlite" in settings.database_url
    else {},
)

# Create async session maker
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def create_db_and_tables() -> None:
    """Create database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session.

    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database session.

    Yields:
        AsyncSession: Database session with automatic transaction management
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db_connection() -> None:
    """Close database connection."""
    await engine.dispose()


# Health check function
async def check_db_health() -> bool:
    """
    Check database connectivity.

    Returns:
        bool: True if database is accessible, False otherwise
    """
    try:
        async with get_db_session() as session:
            # Simple query to check connection
            await session.execute("SELECT 1")
            return True
    except Exception:
        return False
