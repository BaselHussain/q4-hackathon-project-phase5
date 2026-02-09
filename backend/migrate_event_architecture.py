"""
Database migration for Spec 8 - Kafka + Dapr Event-Driven Architecture.

Creates:
- audit_logs table for comprehensive audit trail
- dapr_state table for Dapr State Store (PostgreSQL backend)

Usage:
    python migrate_event_architecture.py
"""
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text


DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")


MIGRATIONS = [
    # Migration 1: Create audit_logs table
    """
    CREATE TABLE IF NOT EXISTS audit_logs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        event_id UUID NOT NULL UNIQUE,
        timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        user_id UUID NOT NULL REFERENCES users(id),
        event_type VARCHAR(50) NOT NULL,
        task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
        payload JSONB NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    # Migration 2: Create indexes for audit_logs
    "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type)",
    "CREATE INDEX IF NOT EXISTS idx_audit_logs_task_id ON audit_logs(task_id)",
    # Migration 3: Create dapr_state table (required by Dapr PostgreSQL state store)
    """
    CREATE TABLE IF NOT EXISTS dapr_state (
        key TEXT PRIMARY KEY,
        value JSONB NOT NULL,
        isbinary BOOLEAN NOT NULL DEFAULT FALSE,
        insertdate TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updatedate TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        etag TEXT
    )
    """,
    # Migration 4: Create index for dapr_state TTL cleanup
    "CREATE INDEX IF NOT EXISTS idx_dapr_state_updatedate ON dapr_state(updatedate)",
]


async def run_migration():
    """Execute all migration statements."""
    engine = create_async_engine(DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        for i, sql in enumerate(MIGRATIONS, 1):
            print(f"Running migration step {i}/{len(MIGRATIONS)}...")
            await conn.execute(text(sql))
            print(f"  Step {i} completed.")

    await engine.dispose()
    print("\nAll migrations completed successfully!")


if __name__ == "__main__":
    asyncio.run(run_migration())
