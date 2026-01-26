"""Check if users table exists in the database."""
import asyncio
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from database import engine
from sqlalchemy import text


async def check_users_table():
    """Check if users table exists."""
    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='public' AND table_name='users'"
            )
        )
        exists = result.fetchone() is not None
        print(f"Users table exists: {exists}")

        if exists:
            # Check columns
            result = await conn.execute(
                text(
                    "SELECT column_name, data_type FROM information_schema.columns "
                    "WHERE table_name='users' ORDER BY ordinal_position"
                )
            )
            print("\nUsers table columns:")
            for row in result:
                print(f"  - {row[0]}: {row[1]}")


if __name__ == "__main__":
    asyncio.run(check_users_table())
