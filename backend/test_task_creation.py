"""Test task creation directly to see the actual error."""
import asyncio
from dotenv import load_dotenv
from uuid import uuid4

load_dotenv()

from database import get_db
from models import Task, TaskStatus


async def test_create_task():
    """Try to create a task and see what error occurs."""
    db_gen = get_db()
    db = await anext(db_gen)

    try:
        # Create a test user_id
        user_id = uuid4()

        # Try to create a task
        new_task = Task(
            id=uuid4(),
            user_id=user_id,
            title="Test Task",
            description="Test description",
            status=TaskStatus.PENDING
        )

        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)

        print(f"✓ Task created successfully: {new_task.id}")
        print(f"  Title: {new_task.title}")
        print(f"  Status: {new_task.status}")

    except Exception as e:
        print(f"✗ Error creating task:")
        print(f"  Type: {type(e).__name__}")
        print(f"  Message: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(test_create_task())
