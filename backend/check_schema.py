"""Check database schema status."""
import asyncio
from dotenv import load_dotenv

load_dotenv()

from database import engine
from sqlalchemy import text


async def check_schema():
    """Check current database schema."""
    async with engine.begin() as conn:
        # Check all tables
        result = await conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='public' ORDER BY table_name"
            )
        )
        print("Tables in database:")
        for row in result:
            print(f"  - {row[0]}")

        # Check tasks table columns
        result = await conn.execute(
            text(
                "SELECT column_name, data_type, is_nullable "
                "FROM information_schema.columns "
                "WHERE table_name='tasks' ORDER BY ordinal_position"
            )
        )
        print("\nTasks table columns:")
        for row in result:
            print(f"  - {row[0]}: {row[1]} (nullable: {row[2]})")


if __name__ == "__main__":
    asyncio.run(check_schema())
