"""Check alembic version."""
import asyncio
from dotenv import load_dotenv

load_dotenv()

from database import engine
from sqlalchemy import text


async def check_alembic():
    """Check alembic version."""
    async with engine.begin() as conn:
        result = await conn.execute(
            text("SELECT version_num FROM alembic_version")
        )
        version = result.fetchone()
        if version:
            print(f"Current alembic version: {version[0]}")
        else:
            print("No alembic version found")


if __name__ == "__main__":
    asyncio.run(check_alembic())
