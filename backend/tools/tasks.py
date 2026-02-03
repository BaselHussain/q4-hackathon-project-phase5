"""
Stateless MCP tools for task management.

Each tool:
- Creates fresh database session (stateless)
- Validates user ownership
- Returns structured JSON response
- Handles errors gracefully

Tools exposed:
- add_task: Create a new task
- list_tasks: List tasks with optional status filter
- complete_task: Mark a task as completed
- delete_task: Permanently remove a task
- update_task: Update task title and/or description
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables before importing database
from dotenv import load_dotenv
load_dotenv()

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.exc import OperationalError
from sqlmodel import select

from database import AsyncSessionLocal
from src.models.task import Task, TaskStatus


# =============================================================================
# Helper Functions (T005-T010)
# =============================================================================

def validate_uuid(value: str, field_name: str = "ID") -> tuple[bool, Optional[UUID], Optional[dict]]:
    """
    Validate that a string is a valid UUID format.

    Args:
        value: String to validate as UUID
        field_name: Name of field for error message

    Returns:
        Tuple of (is_valid, uuid_value, error_response)
        If valid: (True, UUID, None)
        If invalid: (False, None, error_dict)
    """
    try:
        uuid_value = UUID(value)
        return True, uuid_value, None
    except (ValueError, TypeError):
        return False, None, error_response(f"Invalid {field_name} format")


def serialize_task(task: Task) -> dict:
    """
    Convert Task model to JSON-serializable dictionary.

    Args:
        task: Task model instance

    Returns:
        Dictionary with task data suitable for JSON response
    """
    return {
        "task_id": str(task.id),
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }


def success_response(data) -> dict:
    """
    Create a successful response structure.

    Args:
        data: Payload to include in response

    Returns:
        Structured success response
    """
    return {"success": True, "data": data}


def error_response(message: str) -> dict:
    """
    Create an error response structure.

    Args:
        message: User-friendly error message

    Returns:
        Structured error response
    """
    return {"success": False, "error": message}


# =============================================================================
# Tool Registration Function
# =============================================================================

def register_tools(mcp):
    """
    Register all task management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
    """

    # =========================================================================
    # Tool 1: add_task (US1 - P1)
    # =========================================================================

    @mcp.tool()
    async def add_task(user_id: str, title: str, description: str = None) -> dict:
        """
        Create a new task for the user.

        Args:
            user_id: UUID of the user who owns this task
            title: Title of the task (1-200 characters)
            description: Optional description (max 2000 characters)

        Returns:
            Success response with created task data, or error response
        """
        # Validate user_id format
        is_valid, user_uuid, err = validate_uuid(user_id, "user_id")
        if not is_valid:
            return err

        # Validate title (required, 1-200 chars)
        if not title or not title.strip():
            return error_response("Task title is required")

        title = title.strip()
        if len(title) > 200:
            return error_response("Task title must be 200 characters or less")

        # Validate description (optional, max 2000 chars)
        if description is not None:
            description = description.strip() if description else None
            if description and len(description) > 2000:
                return error_response("Task description must be 2000 characters or less")

        # Create task in database
        try:
            async with AsyncSessionLocal() as session:
                new_task = Task(
                    user_id=user_uuid,
                    title=title,
                    description=description,
                    status=TaskStatus.PENDING
                )
                session.add(new_task)
                await session.commit()
                await session.refresh(new_task)

                return success_response(serialize_task(new_task))

        except OperationalError:
            return error_response("Service temporarily unavailable, please try again")
        except Exception as e:
            return error_response("Service temporarily unavailable, please try again")

    # =========================================================================
    # Tool 2: list_tasks (US2 - P1)
    # =========================================================================

    @mcp.tool()
    async def list_tasks(user_id: str, status: str = "all") -> dict:
        """
        List all tasks for a user with optional status filter.

        Args:
            user_id: UUID of the user
            status: Filter by status - "all", "pending", or "completed" (default: "all")

        Returns:
            Success response with array of tasks, or error response
        """
        # Validate user_id format
        is_valid, user_uuid, err = validate_uuid(user_id, "user_id")
        if not is_valid:
            return err

        # Validate status parameter
        valid_statuses = ["all", "pending", "completed"]
        status = status.lower() if status else "all"
        if status not in valid_statuses:
            return error_response(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

        # Query database
        try:
            async with AsyncSessionLocal() as session:
                # Build query with user filter
                query = select(Task).where(Task.user_id == user_uuid)

                # Add status filter if not "all"
                if status == "pending":
                    query = query.where(Task.status == TaskStatus.PENDING)
                elif status == "completed":
                    query = query.where(Task.status == TaskStatus.COMPLETED)

                # Order by created_at descending (newest first)
                query = query.order_by(Task.created_at.desc())

                result = await session.execute(query)
                tasks = result.scalars().all()

                # Serialize all tasks
                task_list = [serialize_task(task) for task in tasks]

                return success_response(task_list)

        except OperationalError:
            return error_response("Service temporarily unavailable, please try again")
        except Exception as e:
            return error_response("Service temporarily unavailable, please try again")

    # =========================================================================
    # Tool 3: complete_task (US3 - P2)
    # =========================================================================

    @mcp.tool()
    async def complete_task(user_id: str, task_id: str) -> dict:
        """
        Mark a task as completed.

        Args:
            user_id: UUID of the user who owns the task
            task_id: UUID of the task to complete

        Returns:
            Success response with updated task data, or error response
        """
        # Validate user_id format
        is_valid, user_uuid, err = validate_uuid(user_id, "user_id")
        if not is_valid:
            return err

        # Validate task_id format
        is_valid, task_uuid, err = validate_uuid(task_id, "task_id")
        if not is_valid:
            return err

        # Find and update task
        try:
            async with AsyncSessionLocal() as session:
                # Get task by ID
                task = await session.get(Task, task_uuid)

                # Check if task exists and belongs to user
                if not task or task.user_id != user_uuid:
                    return error_response("Task not found or access denied")

                # Update status to completed (idempotent - already completed is OK)
                task.status = TaskStatus.COMPLETED
                task.updated_at = datetime.now(timezone.utc)

                await session.commit()
                await session.refresh(task)

                return success_response(serialize_task(task))

        except OperationalError:
            return error_response("Service temporarily unavailable, please try again")
        except Exception as e:
            return error_response("Service temporarily unavailable, please try again")

    # =========================================================================
    # Tool 4: delete_task (US4 - P2)
    # =========================================================================

    @mcp.tool()
    async def delete_task(user_id: str, task_id: str) -> dict:
        """
        Permanently delete a task.

        Args:
            user_id: UUID of the user who owns the task
            task_id: UUID of the task to delete

        Returns:
            Success response with confirmation, or error response
        """
        # Validate user_id format
        is_valid, user_uuid, err = validate_uuid(user_id, "user_id")
        if not is_valid:
            return err

        # Validate task_id format
        is_valid, task_uuid, err = validate_uuid(task_id, "task_id")
        if not is_valid:
            return err

        # Find and delete task
        try:
            async with AsyncSessionLocal() as session:
                # Get task by ID
                task = await session.get(Task, task_uuid)

                # Check if task exists and belongs to user
                if not task or task.user_id != user_uuid:
                    return error_response("Task not found or access denied")

                # Store task_id before deletion
                deleted_task_id = str(task.id)

                # Delete the task
                await session.delete(task)
                await session.commit()

                return success_response({
                    "task_id": deleted_task_id,
                    "message": "Task deleted successfully"
                })

        except OperationalError:
            return error_response("Service temporarily unavailable, please try again")
        except Exception as e:
            return error_response("Service temporarily unavailable, please try again")

    # =========================================================================
    # Tool 5: update_task (US5 - P3)
    # =========================================================================

    @mcp.tool()
    async def update_task(
        user_id: str,
        task_id: str,
        title: str = None,
        description: str = None
    ) -> dict:
        """
        Update a task's title and/or description.

        Args:
            user_id: UUID of the user who owns the task
            task_id: UUID of the task to update
            title: New title for the task (optional, 1-200 characters)
            description: New description for the task (optional, max 2000 characters)

        Returns:
            Success response with updated task data, or error response
        """
        # Validate user_id format
        is_valid, user_uuid, err = validate_uuid(user_id, "user_id")
        if not is_valid:
            return err

        # Validate task_id format
        is_valid, task_uuid, err = validate_uuid(task_id, "task_id")
        if not is_valid:
            return err

        # Validate at least one field is provided
        has_title = title is not None and title.strip() != ""
        has_description = description is not None

        if not has_title and not has_description:
            return error_response("At least one field (title or description) must be provided")

        # Validate title if provided
        if has_title:
            title = title.strip()
            if len(title) > 200:
                return error_response("Task title must be 200 characters or less")
            if len(title) < 1:
                return error_response("Task title must be at least 1 character")

        # Validate description if provided
        if has_description and description:
            description = description.strip()
            if len(description) > 2000:
                return error_response("Task description must be 2000 characters or less")

        # Find and update task
        try:
            async with AsyncSessionLocal() as session:
                # Get task by ID
                task = await session.get(Task, task_uuid)

                # Check if task exists and belongs to user
                if not task or task.user_id != user_uuid:
                    return error_response("Task not found or access denied")

                # Update fields that were provided
                if has_title:
                    task.title = title
                if has_description:
                    task.description = description if description else None

                task.updated_at = datetime.now(timezone.utc)

                await session.commit()
                await session.refresh(task)

                return success_response(serialize_task(task))

        except OperationalError:
            return error_response("Service temporarily unavailable, please try again")
        except Exception as e:
            return error_response("Service temporarily unavailable, please try again")
