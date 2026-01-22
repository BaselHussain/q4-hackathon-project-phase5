"""
Database initialization script.

This script creates all database tables defined in the SQLModel models.
Run this script before starting the application for the first time.

Usage:
    python -m backend.init_db
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from sqlmodel import SQLModel

from backend.database import engine
from backend.models import Task, User  # noqa: F401 - Import models to register them with SQLModel


async def init_db() -> None:
    """
    Initialize the database by creating all tables.

    This function uses SQLModel's metadata to create all tables defined
    in the models. It should be run once before starting the application.
    """
    async with engine.begin() as conn:
        # Create all tables defined in SQLModel metadata
        await conn.run_sync(SQLModel.metadata.create_all)

    print("Database tables created successfully!")


async def main() -> None:
    """Main entry point for the database initialization script."""
    print("Initializing database...")
    await init_db()
    print("Database initialization complete.")


if __name__ == "__main__":
    asyncio.run(main())
