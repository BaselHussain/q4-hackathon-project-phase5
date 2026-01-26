"""Check database tables and create users table if needed."""
import asyncio
from database import engine
from sqlalchemy import text


async def check_and_create_tables():
    """Check what tables exist and create users table if needed."""
    async with engine.begin() as conn:
        # Check existing tables
        result = await conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        )
        tables = [row[0] for row in result]
        print(f"Existing tables: {tables}")

        # Check if users table exists
        if 'users' not in tables:
            print("\nCreating users table...")
            await conn.execute(text("""
                CREATE TABLE users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    email VARCHAR(254) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_login_at TIMESTAMP WITH TIME ZONE
                )
            """))

            # Create index
            await conn.execute(text("""
                CREATE UNIQUE INDEX ix_users_email ON users(email)
            """))

            print("Users table created successfully!")
        else:
            print("\nUsers table already exists!")

        # Check if tasks table has user_id column
        result = await conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='tasks' AND column_name='user_id'
        """))
        has_user_id = len(list(result)) > 0

        if not has_user_id and 'tasks' in tables:
            print("\nAdding user_id column to tasks table...")
            await conn.execute(text("""
                ALTER TABLE tasks ADD COLUMN user_id UUID
            """))

            await conn.execute(text("""
                CREATE INDEX ix_tasks_user_id ON tasks(user_id)
            """))

            await conn.execute(text("""
                ALTER TABLE tasks
                ADD CONSTRAINT fk_tasks_user_id
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            """))

            print("user_id column added to tasks table!")
        else:
            print("\nTasks table already has user_id column!")


if __name__ == "__main__":
    asyncio.run(check_and_create_tables())
