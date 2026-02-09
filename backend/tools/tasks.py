"""
Stateless MCP tools for task management.

Each tool contains the full business logic for its operation.
Tools are registered with the MCP server via register_tools().
"""
import sys
import os
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables before importing database
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import case, func, or_, literal
from sqlalchemy.exc import OperationalError
from sqlmodel import select

from database import AsyncSessionLocal
from src.models.task import Task, TaskStatus, TaskPriority, TaskRecurrence


# =============================================================================
# Helper Functions
# =============================================================================

def validate_uuid(value: str, field_name: str = "ID") -> tuple[bool, Optional[UUID], Optional[dict]]:
    """Validate that a string is a valid UUID format."""
    try:
        uuid_value = UUID(value)
        return True, uuid_value, None
    except (ValueError, TypeError):
        return False, None, error_response(f"Invalid {field_name} format")


def _enum_value(val) -> str:
    """Safely extract .value from an enum, or return the string as-is."""
    return val.value if hasattr(val, "value") else str(val)


def serialize_task(task: Task) -> dict:
    """Convert Task model to JSON-serializable dictionary."""
    return {
        "task_id": str(task.id),
        "title": task.title,
        "description": task.description,
        "status": _enum_value(task.status),
        "priority": _enum_value(task.priority),
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "tags": task.tags if task.tags else [],
        "recurrence": _enum_value(task.recurrence),
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }


def success_response(data) -> dict:
    """Create a successful response structure."""
    return {"success": True, "data": data}


def error_response(message: str) -> dict:
    """Create an error response structure."""
    return {"success": False, "error": message}


# =============================================================================
# Tool Registration
# =============================================================================

def register_tools(mcp):
    """
    Register all task management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
    """

    @mcp.tool()
    async def add_task(
        user_id: str,
        title: str,
        description: str = None,
        due_date: str = None,
        priority: str = "medium",
        tags: str = None,
        recurrence: str = "none",
    ) -> dict:
        """
        Create a new task for the user.

        Args:
            user_id: UUID of the user who owns this task
            title: Title of the task (1-200 characters)
            description: Optional description (max 2000 characters)
            due_date: Optional due date in ISO 8601 format (e.g., "2026-02-14T23:59:00Z")
            priority: Priority level - "high", "medium", or "low" (default: "medium")
            tags: Optional comma-separated tags (e.g., "work,urgent")
            recurrence: Recurrence pattern - "none", "daily", "weekly", "monthly", "yearly" (default: "none")

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

        # Validate and convert priority
        priority = (priority or "medium").lower()
        if priority not in ["high", "medium", "low"]:
            return error_response("Priority must be one of: high, medium, low")

        # Validate and convert recurrence
        recurrence = (recurrence or "none").lower()
        if recurrence not in ["none", "daily", "weekly", "monthly", "yearly"]:
            return error_response("Recurrence must be one of: none, daily, weekly, monthly, yearly")

        # Parse due_date
        parsed_due_date = None
        if due_date:
            try:
                parsed_due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                return error_response("Invalid due_date format. Use ISO 8601 (e.g., 2026-02-14T23:59:00Z)")

        # Parse tags
        parsed_tags = None
        if tags:
            parsed_tags = [t.strip().lower() for t in tags.split(",") if t.strip()]
            if len(parsed_tags) > 10:
                return error_response("Maximum 10 tags per task")
            for tag in parsed_tags:
                if len(tag) > 50:
                    return error_response("Each tag must be 50 characters or less")
            if not parsed_tags:
                parsed_tags = None

        # Create task in database
        try:
            async with AsyncSessionLocal() as session:
                new_task = Task(
                    user_id=user_uuid,
                    title=title,
                    description=description,
                    status=TaskStatus.PENDING,
                    priority=TaskPriority(priority),
                    due_date=parsed_due_date,
                    tags=parsed_tags,
                    recurrence=TaskRecurrence(recurrence),
                )
                session.add(new_task)
                await session.commit()
                await session.refresh(new_task)
                return success_response(serialize_task(new_task))
        except OperationalError:
            return error_response("Service temporarily unavailable, please try again")
        except Exception:
            return error_response("Service temporarily unavailable, please try again")

    @mcp.tool()
    async def list_tasks(
        user_id: str,
        status: str = "all",
        priority: str = None,
        tags: str = None,
        search: str = None,
        sort: str = "created_at",
        order: str = "desc",
        overdue: str = "false",
    ) -> dict:
        """
        List all tasks for a user with optional filtering, searching, and sorting.

        Args:
            user_id: UUID of the user
            status: Filter by status - "all", "pending", or "completed" (default: "all")
            priority: Filter by priority - "high", "medium", or "low" (optional)
            tags: Filter by tags - comma-separated, AND logic (e.g., "work,urgent") (optional)
            search: Case-insensitive search in title and description (optional)
            sort: Sort field - "priority", "due_date", "created_at", "status" (default: "created_at")
            order: Sort direction - "asc" or "desc" (default: "desc")
            overdue: Show only overdue tasks - "true" or "false" (default: "false")

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

        # Validate sort field
        valid_sort_fields = ["priority", "due_date", "created_at", "status"]
        sort = (sort or "created_at").lower()
        if sort not in valid_sort_fields:
            return error_response(f"Invalid sort field. Must be one of: {', '.join(valid_sort_fields)}")

        # Validate priority filter
        if priority:
            priority = priority.lower()
            if priority not in ["high", "medium", "low"]:
                return error_response("Invalid priority. Must be one of: high, medium, low")

        order = (order or "desc").lower()

        # Query database
        try:
            async with AsyncSessionLocal() as session:
                query = select(Task).where(Task.user_id == user_uuid)

                # Status filter
                if status == "pending":
                    query = query.where(Task.status == TaskStatus.PENDING)
                elif status == "completed":
                    query = query.where(Task.status == TaskStatus.COMPLETED)

                # Priority filter
                if priority:
                    query = query.where(Task.priority == TaskPriority(priority))

                # Tags filter (AND logic — each tag must be present)
                if tags:
                    tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()]
                    for tag in tag_list:
                        query = query.where(literal(tag) == func.any(Task.tags))

                # Search filter
                if search:
                    search_pattern = f"%{search}%"
                    query = query.where(
                        or_(
                            Task.title.ilike(search_pattern),
                            Task.description.ilike(search_pattern),
                        )
                    )

                # Overdue filter
                if overdue and overdue.lower() == "true":
                    query = query.where(Task.due_date < func.now(), Task.status == TaskStatus.PENDING)

                # Sort logic
                if sort == "priority":
                    priority_order = case(
                        (Task.priority == TaskPriority.HIGH, 1),
                        (Task.priority == TaskPriority.MEDIUM, 2),
                        (Task.priority == TaskPriority.LOW, 3),
                        else_=4,
                    )
                    primary_sort = priority_order.asc() if order == "asc" else priority_order.desc()
                elif sort == "due_date":
                    primary_sort = Task.due_date.asc().nullslast() if order == "asc" else Task.due_date.desc().nullslast()
                elif sort == "status":
                    primary_sort = Task.status.asc() if order == "asc" else Task.status.desc()
                else:
                    primary_sort = Task.created_at.asc() if order == "asc" else Task.created_at.desc()

                query = query.order_by(primary_sort, Task.due_date.asc().nullslast(), Task.created_at.desc())

                result = await session.execute(query)
                tasks = result.scalars().all()
                task_list = [serialize_task(task) for task in tasks]
                return success_response(task_list)
        except OperationalError:
            return error_response("Service temporarily unavailable, please try again")
        except Exception as e:
            import traceback
            traceback.print_exc()
            return error_response(f"Error: {type(e).__name__}: {e}")

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
                task = await session.get(Task, task_uuid)

                if not task or task.user_id != user_uuid:
                    return error_response("Task not found or access denied")

                task.status = TaskStatus.COMPLETED
                task.updated_at = datetime.now(timezone.utc)

                await session.commit()
                await session.refresh(task)
                return success_response(serialize_task(task))
        except OperationalError:
            return error_response("Service temporarily unavailable, please try again")
        except Exception:
            return error_response("Service temporarily unavailable, please try again")

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
                task = await session.get(Task, task_uuid)

                if not task or task.user_id != user_uuid:
                    return error_response("Task not found or access denied")

                deleted_task_id = str(task.id)
                await session.delete(task)
                await session.commit()
                return success_response({
                    "task_id": deleted_task_id,
                    "message": "Task deleted successfully"
                })
        except OperationalError:
            return error_response("Service temporarily unavailable, please try again")
        except Exception:
            return error_response("Service temporarily unavailable, please try again")

    @mcp.tool()
    async def update_task(
        user_id: str,
        task_id: str,
        title: str = None,
        description: str = None,
        due_date: str = None,
        priority: str = None,
        tags: str = None,
        recurrence: str = None,
    ) -> dict:
        """
        Update a task's fields.

        Args:
            user_id: UUID of the user who owns the task
            task_id: UUID of the task to update
            title: New title for the task (optional, 1-200 characters)
            description: New description for the task (optional, max 2000 characters)
            due_date: New due date in ISO 8601 format (optional)
            priority: New priority - "high", "medium", or "low" (optional)
            tags: New tags as comma-separated string (optional, e.g., "work,urgent")
            recurrence: New recurrence - "none", "daily", "weekly", "monthly", "yearly" (optional)

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
        has_due_date = due_date is not None
        has_priority = priority is not None
        has_tags = tags is not None
        has_recurrence = recurrence is not None

        if not any([has_title, has_description, has_due_date, has_priority, has_tags, has_recurrence]):
            return error_response("At least one field must be provided")

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

        # Validate priority if provided
        if has_priority:
            priority = priority.lower()
            if priority not in ["high", "medium", "low"]:
                return error_response("Priority must be one of: high, medium, low")

        # Validate recurrence if provided
        if has_recurrence:
            recurrence = recurrence.lower()
            if recurrence not in ["none", "daily", "weekly", "monthly", "yearly"]:
                return error_response("Recurrence must be one of: none, daily, weekly, monthly, yearly")

        # Parse due_date if provided
        parsed_due_date = None
        if has_due_date:
            try:
                parsed_due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                return error_response("Invalid due_date format. Use ISO 8601 (e.g., 2026-02-14T23:59:00Z)")

        # Parse tags if provided
        parsed_tags = None
        if has_tags:
            if tags.strip():
                parsed_tags = [t.strip().lower() for t in tags.split(",") if t.strip()]
                if len(parsed_tags) > 10:
                    return error_response("Maximum 10 tags per task")
                for tag in parsed_tags:
                    if len(tag) > 50:
                        return error_response("Each tag must be 50 characters or less")
                if not parsed_tags:
                    parsed_tags = None

        # Find and update task
        try:
            async with AsyncSessionLocal() as session:
                task = await session.get(Task, task_uuid)

                if not task or task.user_id != user_uuid:
                    return error_response("Task not found or access denied")

                if has_title:
                    task.title = title
                if has_description:
                    task.description = description if description else None
                if has_priority:
                    task.priority = TaskPriority(priority)
                if has_due_date:
                    task.due_date = parsed_due_date
                if has_tags:
                    task.tags = parsed_tags
                if has_recurrence:
                    task.recurrence = TaskRecurrence(recurrence)

                task.updated_at = datetime.now(timezone.utc)

                await session.commit()
                await session.refresh(task)
                return success_response(serialize_task(task))
        except OperationalError:
            return error_response("Service temporarily unavailable, please try again")
        except Exception:
            return error_response("Service temporarily unavailable, please try again")
