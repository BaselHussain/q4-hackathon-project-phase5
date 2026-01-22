"""
Database configuration and session management.

This module provides async database engine, session factory, and dependency injection
for database sessions with connection pooling and retry logic.
"""
import asyncio
import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError


# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Create async engine with asyncpg driver
# echo=True enables SQL query logging for development
# T066: Connection pooling configuration
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
    pool_size=10,           # Maximum number of connections in the pool
    max_overflow=20,        # Maximum number of connections that can be created beyond pool_size
    pool_pre_ping=True,     # Verify connections before using them
    pool_recycle=3600       # Recycle connections after 1 hour
)

# Create async session factory
# expire_on_commit=False prevents attributes from expiring after commit
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function that provides database sessions.

    Yields an AsyncSession and ensures proper cleanup after use.
    Use this as a FastAPI dependency for endpoints that need database access.

    T067: Implements retry logic with exponential backoff for connection failures.

    Yields:
        AsyncSession: Database session for executing queries

    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    max_retries = 3
    retry_delay = 1  # Initial delay in seconds

    for attempt in range(max_retries):
        try:
            async with AsyncSessionLocal() as session:
                yield session
                return
        except OperationalError as e:
            if attempt < max_retries - 1:
                # Exponential backoff: wait 1s, 2s, 4s
                await asyncio.sleep(retry_delay * (2 ** attempt))
                continue
            else:
                # Final attempt failed, raise the error
                raise
        finally:
            # Ensure session is closed even if error occurs
            pass
