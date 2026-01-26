"""
Pytest configuration and fixtures for integration tests.

Provides test fixtures for database sessions, test client, and test data.
"""
import asyncio
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

# Load environment variables before anything else
load_dotenv()

# Import models BEFORE importing app to ensure they're registered
from src.models.user import User
from src.models.task import Task, TaskStatus


# Test database URL (use a separate test database)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    os.getenv("DATABASE_URL")  # Fallback to main database if test DB not configured
)


# Create schema synchronously at module import time (before app is imported)
def _setup_schema():
    """Set up database schema before any tests run."""
    async def _async_setup():
        # Terminate all existing connections to avoid prepared statement cache issues
        engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
        async with engine.begin() as conn:
            # Terminate all connections to this database (except our own)
            await conn.execute(text("""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = current_database()
                AND pid <> pg_backend_pid()
            """))
        await engine.dispose()

        # Now drop and recreate schema
        engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
        async with engine.begin() as conn:
            await conn.execute(text("DROP TYPE IF EXISTS taskstatus CASCADE"))
            await conn.run_sync(SQLModel.metadata.drop_all)
        await engine.dispose()

        # Create fresh schema
        engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        await engine.dispose()

    asyncio.run(_async_setup())


# Set up schema before importing app
_setup_schema()

# Import app AFTER database schema is set up
from main import app
from database import get_db


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a database session for tests.

    Truncates tables before and after each test for isolation.
    Schema and ENUM types are preserved across all tests.
    """
    # Create a fresh engine for this test
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
        poolclass=NullPool
    )

    # Create session factory
    TestSessionLocal = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )

    # Truncate all tables before test
    async with test_engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE tasks, users CASCADE"))

    # Provide session
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

    # Truncate all tables after test
    async with test_engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE tasks, users CASCADE"))

    # Dispose test engine
    await test_engine.dispose()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an async HTTP client for testing API endpoints.

    Overrides the get_db dependency to use the test database session.
    """
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    # Use ASGITransport for httpx 0.23+
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
