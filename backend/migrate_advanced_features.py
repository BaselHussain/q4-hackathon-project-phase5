"""
Database migration script for advanced todo features.

Adds priority, due_date, tags, and recurrence columns to the tasks table.
All statements are idempotent (safe to run multiple times).
"""
import asyncio
import sys

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from database import engine


MIGRATION_STATEMENTS = [
    "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS priority VARCHAR(10) NOT NULL DEFAULT 'medium'",
    "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS due_date TIMESTAMPTZ",
    "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS tags TEXT[]",
    "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS recurrence VARCHAR(10) NOT NULL DEFAULT 'none'",
    "CREATE INDEX IF NOT EXISTS ix_tasks_priority ON tasks (priority)",
    "CREATE INDEX IF NOT EXISTS ix_tasks_due_date ON tasks (due_date)",
    "CREATE INDEX IF NOT EXISTS ix_tasks_user_priority ON tasks (user_id, priority)",
    "CREATE INDEX IF NOT EXISTS ix_tasks_user_due_date ON tasks (user_id, due_date)",
]


async def run_migration():
    """Execute the migration statements against the database."""
    print("Starting advanced features migration...")

    async with engine.begin() as conn:
        for stmt in MIGRATION_STATEMENTS:
            print(f"  Executing: {stmt[:80]}...")
            await conn.execute(text(stmt))

    # Verify columns exist
    async with engine.begin() as conn:
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'tasks' AND column_name IN ('priority', 'due_date', 'tags', 'recurrence') "
            "ORDER BY column_name"
        ))
        columns = [row[0] for row in result.fetchall()]
        print(f"\nVerification - columns found: {columns}")

        expected = ["due_date", "priority", "recurrence", "tags"]
        if columns == expected:
            print("Migration successful! All 4 new columns exist.")
        else:
            missing = set(expected) - set(columns)
            print(f"WARNING: Missing columns: {missing}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_migration())
