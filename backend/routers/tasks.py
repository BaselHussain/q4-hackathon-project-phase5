"""
Tasks router for Task Management API.

This module implements endpoints for task operations including listing,
creating, updating, and deleting tasks. All endpoints require JWT authentication.
Event publishing via Dapr Pub/Sub is integrated for event-driven architecture.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError
from sqlalchemy import case, func, literal, or_, select
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from src.api.dependencies import get_current_user, verify_user_access
from models import Task, TaskStatus, TaskPriority, TaskRecurrence
from schemas import TaskCreate, TaskResponse, TaskUpdate
from events.publisher import publish_task_event, publish_reminder_event, publish_sync_event
from events.schemas import TaskEventType, TaskEventPayload, ReminderEventType

logger = logging.getLogger(__name__)

# Create router with prefix and tags
# T046-T050: Update prefix to include user_id path parameter
router = APIRouter(
    prefix="/api/{user_id}/tasks",
    tags=["tasks"]
)


VALID_SORT_FIELDS = ["priority", "due_date", "created_at", "status"]


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    user_id: Annotated[UUID, Depends(verify_user_access)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: Optional[str] = Query("all", description="Filter by status: all, pending, completed"),
    priority: Optional[str] = Query(None, description="Filter by priority: high, medium, low"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated, AND logic)"),
    due_before: Optional[datetime] = Query(None, description="Tasks due before this date"),
    due_after: Optional[datetime] = Query(None, description="Tasks due after this date"),
    overdue: Optional[bool] = Query(False, description="Show only overdue tasks"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    sort: Optional[str] = Query("created_at", description="Sort field: priority, due_date, created_at, status"),
    order: Optional[str] = Query("desc", description="Sort direction: asc, desc"),
) -> List[TaskResponse]:
    """
    Get all tasks for the authenticated user with optional filtering, searching, and sorting.

    Args:
        user_id: User ID from URL path parameter (validated by verify_user_access)
        db: Database session
        status: Filter by task status
        priority: Filter by priority level
        tags: Comma-separated tags to filter by (AND logic)
        due_before: Filter tasks due before this datetime
        due_after: Filter tasks due after this datetime
        overdue: If true, only return overdue tasks
        search: Case-insensitive search in title and description
        sort: Field to sort by
        order: Sort direction (asc/desc)

    Returns:
        List[TaskResponse]: Filtered, sorted list of tasks

    Raises:
        HTTPException: 401 if token is missing or invalid
        HTTPException: 403 if user_id doesn't match token user_id
        HTTPException: 422 if invalid filter/sort parameters
        HTTPException: 503 error if database is temporarily unavailable
    """
    try:
        # Validate sort field
        if sort and sort not in VALID_SORT_FIELDS:
            raise HTTPException(
                status_code=422,
                detail={
                    "type": "validation-error",
                    "title": "Validation Error",
                    "detail": f"Invalid sort field. Must be one of: {', '.join(VALID_SORT_FIELDS)}",
                    "status": 422
                }
            )

        # Validate priority filter
        if priority:
            try:
                TaskPriority(priority.lower())
            except ValueError:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "type": "validation-error",
                        "title": "Validation Error",
                        "detail": "Invalid priority. Must be one of: high, medium, low",
                        "status": 422
                    }
                )

        # Build base query
        stmt = select(Task).where(Task.user_id == user_id)

        # Status filter
        if status and status != "all":
            if status == "pending":
                stmt = stmt.where(Task.status == TaskStatus.PENDING)
            elif status == "completed":
                stmt = stmt.where(Task.status == TaskStatus.COMPLETED)

        # Priority filter
        if priority:
            stmt = stmt.where(Task.priority == TaskPriority(priority.lower()))

        # Tags filter (AND logic — task must have ALL specified tags)
        if tags:
            tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()]
            for tag in tag_list:
                stmt = stmt.where(literal(tag) == func.any(Task.tags))

        # Due date range filters
        if due_before:
            stmt = stmt.where(Task.due_date <= due_before)
        if due_after:
            stmt = stmt.where(Task.due_date >= due_after)

        # Overdue filter
        if overdue:
            stmt = stmt.where(Task.due_date < func.now(), Task.status == TaskStatus.PENDING)

        # Search filter (case-insensitive ILIKE on title and description)
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Task.title.ilike(search_pattern),
                    Task.description.ilike(search_pattern),
                )
            )

        # Sort logic
        sort_field = sort or "created_at"
        sort_dir = order or "desc"

        if sort_field == "priority":
            # Custom priority ordering: high=1, medium=2, low=3
            priority_order = case(
                (Task.priority == TaskPriority.HIGH, 1),
                (Task.priority == TaskPriority.MEDIUM, 2),
                (Task.priority == TaskPriority.LOW, 3),
                else_=4,
            )
            primary_sort = priority_order.asc() if sort_dir == "asc" else priority_order.desc()
        elif sort_field == "due_date":
            # Nulls last for due_date sorting
            if sort_dir == "asc":
                primary_sort = Task.due_date.asc().nullslast()
            else:
                primary_sort = Task.due_date.desc().nullslast()
        elif sort_field == "status":
            if sort_dir == "asc":
                primary_sort = Task.status.asc()
            else:
                primary_sort = Task.status.desc()
        else:
            # Default: created_at
            if sort_dir == "asc":
                primary_sort = Task.created_at.asc()
            else:
                primary_sort = Task.created_at.desc()

        # Apply sort with secondary sorts
        stmt = stmt.order_by(primary_sort, Task.due_date.asc().nullslast(), Task.created_at.desc())

        result = await db.execute(stmt)
        tasks = result.scalars().all()

        return [TaskResponse.model_validate(task) for task in tasks]

    except HTTPException:
        raise

    except (DBAPIError, OperationalError) as e:
        raise HTTPException(
            status_code=503,
            detail={
                "type": "service-unavailable",
                "title": "Service Unavailable",
                "detail": "Database temporarily unavailable",
                "status": 503
            }
        )


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    task_data: TaskCreate,
    user_id: Annotated[UUID, Depends(verify_user_access)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TaskResponse:
    """
    Create a new task for the authenticated user.

    Creates a new task with the provided title and optional description.
    The task is automatically assigned to the authenticated user.
    Requires valid JWT token in Authorization header.

    Args:
        task_data: Task creation data (title and optional description)
        user_id: User ID from URL path parameter (validated by verify_user_access)
        db: Database session

    Returns:
        TaskResponse: The newly created task with status="pending" and 201 Created status

    Raises:
        HTTPException: 400 error if validation fails (title/description constraints)
        HTTPException: 401 if token is missing or invalid
        HTTPException: 403 if user_id doesn't match token user_id
        HTTPException: 503 error if database is temporarily unavailable
    """
    try:
        # T028: Generate UUID for new task
        task_id = uuid4()

        # T027-T030: Create new task instance with all required fields
        # Normalize empty tags to None
        task_tags = task_data.tags if task_data.tags else None

        new_task = Task(
            id=task_id,
            user_id=user_id,
            title=task_data.title,
            description=task_data.description,
            status=TaskStatus.PENDING,
            priority=TaskPriority(task_data.priority) if task_data.priority else TaskPriority.MEDIUM,
            due_date=task_data.due_date,
            tags=task_tags,
            recurrence=TaskRecurrence(task_data.recurrence) if task_data.recurrence else TaskRecurrence.NONE,
        )

        # T034: Save to database and return with 201 Created
        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)

        # Publish task.created event (fire-and-forget, don't block response)
        try:
            payload = TaskEventPayload(
                title=new_task.title,
                description=new_task.description,
                status=new_task.status.value,
                priority=new_task.priority.value if hasattr(new_task.priority, 'value') else str(new_task.priority),
                tags=new_task.tags,
                due_date=new_task.due_date.isoformat() if new_task.due_date else None,
                recurring_pattern=new_task.recurrence.value if hasattr(new_task.recurrence, 'value') else str(new_task.recurrence),
            )
            await publish_task_event(
                event_type=TaskEventType.CREATED,
                task_id=new_task.id,
                user_id=user_id,
                payload=payload,
            )

            # Publish sync event for real-time updates
            await publish_sync_event(
                task_id=new_task.id,
                user_id=user_id,
                changed_fields={"action": "created", "title": new_task.title, "status": new_task.status.value},
            )

            # If task has due date, schedule reminder (15 min before)
            if new_task.due_date:
                reminder_time = new_task.due_date - timedelta(minutes=15)
                if reminder_time > datetime.now(timezone.utc):
                    await publish_reminder_event(
                        event_type=ReminderEventType.SCHEDULE,
                        task_id=new_task.id,
                        user_id=user_id,
                        due_date=new_task.due_date,
                        reminder_time=reminder_time,
                    )
        except Exception as e:
            logger.warning(f"Event publishing failed for task create: {e}")

        return TaskResponse.model_validate(new_task)

    except ValidationError as e:
        # T035: Handle Pydantic validation errors with RFC 7807 format
        error_messages = []
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            error_messages.append(f"{field}: {error['msg']}")

        raise HTTPException(
            status_code=400,
            detail={
                "type": "validation-error",
                "title": "Validation Error",
                "detail": "; ".join(error_messages),
                "status": 400
            }
        )

    except (DBAPIError, OperationalError) as e:
        # T035: Handle database errors with RFC 7807 format
        raise HTTPException(
            status_code=503,
            detail={
                "type": "service-unavailable",
                "title": "Service Unavailable",
                "detail": "Database temporarily unavailable",
                "status": 503
            }
        )


@router.patch("/{task_id}/complete", response_model=TaskResponse)
async def toggle_task_completion(
    task_id: UUID,
    user_id: Annotated[UUID, Depends(verify_user_access)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TaskResponse:
    """
    Toggle task completion status between pending and completed.

    Marks a pending task as completed, or a completed task as pending.
    Only the task owner can toggle completion status.
    Requires valid JWT token in Authorization header.

    Args:
        task_id: UUID of the task to toggle
        user_id: User ID from URL path parameter
        current_user_id: User ID extracted from JWT token
        _: Ensures user can only access their own tasks
        db: Database session

    Returns:
        TaskResponse: The updated task with toggled status and 200 OK status

    Raises:
        HTTPException: 400 error if task_id is invalid UUID format
        HTTPException: 401 if token is missing or invalid
        HTTPException: 403 error if user doesn't own the task
        HTTPException: 404 error if task doesn't exist
        HTTPException: 503 error if database is temporarily unavailable
    """
    try:
        # T043: Validate task_id UUID format (handled by FastAPI path parameter type)
        # T037: Query task by id AND user_id to enforce ownership
        stmt = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()

        # T038: Return 404 if task doesn't exist or belongs to different user
        if task is None:
            # Check if task exists at all (for better error message)
            stmt_exists = select(Task).where(Task.id == task_id)
            result_exists = await db.execute(stmt_exists)
            task_exists = result_exists.scalar_one_or_none()

            if task_exists is None:
                # T038: Task doesn't exist
                raise HTTPException(
                    status_code=404,
                    detail={
                        "type": "task-not-found",
                        "title": "Task Not Found",
                        "detail": f"Task with id {task_id} does not exist",
                        "status": 404
                    }
                )
            else:
                # T039: Task exists but belongs to different user
                raise HTTPException(
                    status_code=403,
                    detail={
                        "type": "access-denied",
                        "title": "Access Denied",
                        "detail": "You do not have permission to access this task",
                        "status": 403
                    }
                )

        # T040: Toggle status between "pending" and "completed"
        if task.status == TaskStatus.PENDING:
            task.status = TaskStatus.COMPLETED
        else:
            task.status = TaskStatus.PENDING

        # T041: Update updated_at timestamp (handled automatically by onupdate trigger)
        await db.commit()
        await db.refresh(task)

        # Publish task.completed or task.updated event
        try:
            event_type = TaskEventType.COMPLETED if task.status == TaskStatus.COMPLETED else TaskEventType.UPDATED
            payload = TaskEventPayload(
                title=task.title,
                description=task.description,
                status=task.status.value,
                priority=task.priority.value if hasattr(task.priority, 'value') else str(task.priority),
                tags=task.tags,
                due_date=task.due_date.isoformat() if task.due_date else None,
                recurring_pattern=task.recurrence.value if hasattr(task.recurrence, 'value') else str(task.recurrence),
                changed_fields=["status"],
            )
            await publish_task_event(
                event_type=event_type,
                task_id=task.id,
                user_id=user_id,
                payload=payload,
            )

            await publish_sync_event(
                task_id=task.id,
                user_id=user_id,
                changed_fields={"status": task.status.value},
            )

            # If task completed and had due date, cancel reminder
            if task.status == TaskStatus.COMPLETED and task.due_date:
                await publish_reminder_event(
                    event_type=ReminderEventType.CANCEL,
                    task_id=task.id,
                    user_id=user_id,
                    due_date=task.due_date,
                    reminder_time=task.due_date,
                )
        except Exception as e:
            logger.warning(f"Event publishing failed for task completion toggle: {e}")

        # T042: Return 200 OK with updated TaskResponse
        return TaskResponse.model_validate(task)

    except HTTPException:
        # Re-raise HTTP exceptions (already formatted)
        raise

    except ValueError as e:
        # T043: Handle invalid UUID format
        raise HTTPException(
            status_code=400,
            detail={
                "type": "invalid-identifier",
                "title": "Invalid Identifier",
                "detail": f"Invalid task_id format: {str(e)}",
                "status": 400
            }
        )

    except (DBAPIError, OperationalError) as e:
        # Handle database errors with RFC 7807 format
        raise HTTPException(
            status_code=503,
            detail={
                "type": "service-unavailable",
                "title": "Service Unavailable",
                "detail": "Database temporarily unavailable",
                "status": 503
            }
        )


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_data: TaskUpdate,
    user_id: Annotated[UUID, Depends(verify_user_access)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TaskResponse:
    """
    Update task title and/or description.

    Updates one or more fields of an existing task. At least one field must be provided.
    Only the task owner can update the task. Status and created_at are preserved.
    Requires valid JWT token in Authorization header.

    Args:
        task_id: UUID of the task to update
        task_data: Task update data (title and/or description)
        user_id: User ID from URL path parameter
        current_user_id: User ID extracted from JWT token
        _: Ensures user can only access their own tasks
        db: Database session

    Returns:
        TaskResponse: The updated task with 200 OK status

    Raises:
        HTTPException: 400 error if no fields provided or validation fails
        HTTPException: 401 if token is missing or invalid
        HTTPException: 403 error if user doesn't own the task
        HTTPException: 404 error if task doesn't exist
        HTTPException: 503 error if database is temporarily unavailable
    """
    try:
        # T045: Query task by id AND user_id to enforce ownership
        stmt = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()

        # T046: Return 404 if task doesn't exist
        if task is None:
            # Check if task exists at all (for better error message)
            stmt_exists = select(Task).where(Task.id == task_id)
            result_exists = await db.execute(stmt_exists)
            task_exists = result_exists.scalar_one_or_none()

            if task_exists is None:
                # T046: Task doesn't exist
                raise HTTPException(
                    status_code=404,
                    detail={
                        "type": "task-not-found",
                        "title": "Task Not Found",
                        "detail": f"Task with id {task_id} does not exist",
                        "status": 404
                    }
                )
            else:
                # T047: Task exists but belongs to different user
                raise HTTPException(
                    status_code=403,
                    detail={
                        "type": "access-denied",
                        "title": "Access Denied",
                        "detail": "You do not have permission to access this task",
                        "status": 403
                    }
                )

        # T048: Update only provided fields
        # T051: Validation of at least one field is handled by TaskUpdate schema
        if task_data.title is not None:
            task.title = task_data.title
        if task_data.description is not None:
            task.description = task_data.description
        if task_data.priority is not None:
            task.priority = TaskPriority(task_data.priority)
        if task_data.due_date is not None:
            task.due_date = task_data.due_date
        if task_data.tags is not None:
            task.tags = task_data.tags if task_data.tags else None
        if task_data.recurrence is not None:
            task.recurrence = TaskRecurrence(task_data.recurrence)

        # T049: Preserve status and created_at fields (not modified)
        # T050: Update updated_at timestamp (handled automatically by onupdate trigger)

        # Track changed fields for event publishing
        changed = []
        if task_data.title is not None:
            changed.append("title")
        if task_data.description is not None:
            changed.append("description")
        if task_data.priority is not None:
            changed.append("priority")
        if task_data.due_date is not None:
            changed.append("due_date")
        if task_data.tags is not None:
            changed.append("tags")
        if task_data.recurrence is not None:
            changed.append("recurrence")

        await db.commit()
        await db.refresh(task)

        # Publish task.updated event
        try:
            payload = TaskEventPayload(
                title=task.title,
                description=task.description,
                status=task.status.value,
                priority=task.priority.value if hasattr(task.priority, 'value') else str(task.priority),
                tags=task.tags,
                due_date=task.due_date.isoformat() if task.due_date else None,
                recurring_pattern=task.recurrence.value if hasattr(task.recurrence, 'value') else str(task.recurrence),
                changed_fields=changed,
            )
            await publish_task_event(
                event_type=TaskEventType.UPDATED,
                task_id=task.id,
                user_id=user_id,
                payload=payload,
            )

            sync_changes = {field: getattr(task_data, field) for field in changed if hasattr(task_data, field)}
            await publish_sync_event(
                task_id=task.id,
                user_id=user_id,
                changed_fields=sync_changes,
            )

            # If due_date changed, reschedule reminder
            if "due_date" in changed and task.due_date:
                reminder_time = task.due_date - timedelta(minutes=15)
                if reminder_time > datetime.now(timezone.utc):
                    await publish_reminder_event(
                        event_type=ReminderEventType.SCHEDULE,
                        task_id=task.id,
                        user_id=user_id,
                        due_date=task.due_date,
                        reminder_time=reminder_time,
                    )
        except Exception as e:
            logger.warning(f"Event publishing failed for task update: {e}")

        # T052: Return 200 OK with updated TaskResponse
        return TaskResponse.model_validate(task)

    except HTTPException:
        # Re-raise HTTP exceptions (already formatted)
        raise

    except ValueError as e:
        # Handle validation errors (including minProperties=1 check from TaskUpdate)
        raise HTTPException(
            status_code=400,
            detail={
                "type": "validation-error",
                "title": "Validation Error",
                "detail": str(e),
                "status": 400
            }
        )

    except (DBAPIError, OperationalError) as e:
        # Handle database errors with RFC 7807 format
        raise HTTPException(
            status_code=503,
            detail={
                "type": "service-unavailable",
                "title": "Service Unavailable",
                "detail": "Database temporarily unavailable",
                "status": 503
            }
        )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    user_id: Annotated[UUID, Depends(verify_user_access)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TaskResponse:
    """
    Get a single task by ID.

    Retrieves complete details of a specific task. Only the task owner can view the task.
    Requires valid JWT token in Authorization header.

    Args:
        task_id: UUID of the task to retrieve
        user_id: User ID from URL path parameter
        current_user_id: User ID extracted from JWT token
        _: Ensures user can only access their own tasks
        db: Database session

    Returns:
        TaskResponse: The task with all fields and 200 OK status

    Raises:
        HTTPException: 400 error if task_id is invalid UUID format
        HTTPException: 401 if token is missing or invalid
        HTTPException: 403 error if user doesn't own the task
        HTTPException: 404 error if task doesn't exist
        HTTPException: 503 error if database is temporarily unavailable
    """
    try:
        # T054: Query task by id AND user_id to enforce ownership
        stmt = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()

        # T055: Return 404 if task doesn't exist
        if task is None:
            # Check if task exists at all (for better error message)
            stmt_exists = select(Task).where(Task.id == task_id)
            result_exists = await db.execute(stmt_exists)
            task_exists = result_exists.scalar_one_or_none()

            if task_exists is None:
                # T055: Task doesn't exist
                raise HTTPException(
                    status_code=404,
                    detail={
                        "type": "task-not-found",
                        "title": "Task Not Found",
                        "detail": f"Task with id {task_id} does not exist",
                        "status": 404
                    }
                )
            else:
                # T056: Task exists but belongs to different user
                raise HTTPException(
                    status_code=403,
                    detail={
                        "type": "access-denied",
                        "title": "Access Denied",
                        "detail": "You do not have permission to access this task",
                        "status": 403
                    }
                )

        # T057: Return 200 OK with TaskResponse including all fields
        return TaskResponse.model_validate(task)

    except HTTPException:
        # Re-raise HTTP exceptions (already formatted)
        raise

    except ValueError as e:
        # T058: Handle invalid UUID format
        raise HTTPException(
            status_code=400,
            detail={
                "type": "invalid-identifier",
                "title": "Invalid Identifier",
                "detail": f"Invalid task_id format: {str(e)}",
                "status": 400
            }
        )

    except (DBAPIError, OperationalError) as e:
        # Handle database errors with RFC 7807 format
        raise HTTPException(
            status_code=503,
            detail={
                "type": "service-unavailable",
                "title": "Service Unavailable",
                "detail": "Database temporarily unavailable",
                "status": 503
            }
        )


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: UUID,
    user_id: Annotated[UUID, Depends(verify_user_access)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> None:
    """
    Delete a task permanently.

    Removes a task from the database. Only the task owner can delete the task.
    This operation cannot be undone.
    Requires valid JWT token in Authorization header.

    Args:
        task_id: UUID of the task to delete
        user_id: User ID from URL path parameter
        current_user_id: User ID extracted from JWT token
        _: Ensures user can only access their own tasks
        db: Database session

    Returns:
        None: 204 No Content on successful deletion

    Raises:
        HTTPException: 400 error if task_id is invalid UUID format
        HTTPException: 401 if token is missing or invalid
        HTTPException: 403 error if user doesn't own the task
        HTTPException: 404 error if task doesn't exist
        HTTPException: 503 error if database is temporarily unavailable
    """
    try:
        # T060: Query task by id AND user_id to enforce ownership
        stmt = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()

        # T061: Return 404 if task doesn't exist
        if task is None:
            # Check if task exists at all (for better error message)
            stmt_exists = select(Task).where(Task.id == task_id)
            result_exists = await db.execute(stmt_exists)
            task_exists = result_exists.scalar_one_or_none()

            if task_exists is None:
                # T061: Task doesn't exist
                raise HTTPException(
                    status_code=404,
                    detail={
                        "type": "task-not-found",
                        "title": "Task Not Found",
                        "detail": f"Task with id {task_id} does not exist",
                        "status": 404
                    }
                )
            else:
                # T062: Task exists but belongs to different user
                raise HTTPException(
                    status_code=403,
                    detail={
                        "type": "access-denied",
                        "title": "Access Denied",
                        "detail": "You do not have permission to access this task",
                        "status": 403
                    }
                )

        # Capture task data before deletion for event publishing
        task_title = task.title
        task_description = task.description
        task_status = task.status.value
        task_priority = task.priority.value if hasattr(task.priority, 'value') else str(task.priority)
        task_tags = task.tags
        task_due_date = task.due_date
        task_recurrence = task.recurrence.value if hasattr(task.recurrence, 'value') else str(task.recurrence)

        # T063: Delete task from database
        await db.delete(task)
        await db.commit()

        # Publish task.deleted event
        try:
            payload = TaskEventPayload(
                title=task_title,
                description=task_description,
                status=task_status,
                priority=task_priority,
                tags=task_tags,
                due_date=task_due_date.isoformat() if task_due_date else None,
                recurring_pattern=task_recurrence,
            )
            await publish_task_event(
                event_type=TaskEventType.DELETED,
                task_id=task_id,
                user_id=user_id,
                payload=payload,
            )

            await publish_sync_event(
                task_id=task_id,
                user_id=user_id,
                changed_fields={"action": "deleted"},
            )

            # Cancel any scheduled reminders for this task
            if task_due_date:
                await publish_reminder_event(
                    event_type=ReminderEventType.CANCEL,
                    task_id=task_id,
                    user_id=user_id,
                    due_date=task_due_date,
                    reminder_time=task_due_date,
                )
        except Exception as e:
            logger.warning(f"Event publishing failed for task delete: {e}")

        # T064: Return 204 No Content (handled by status_code=204 in decorator)
        return None

    except HTTPException:
        # Re-raise HTTP exceptions (already formatted)
        raise

    except ValueError as e:
        # T065: Handle invalid UUID format
        raise HTTPException(
            status_code=400,
            detail={
                "type": "invalid-identifier",
                "title": "Invalid Identifier",
                "detail": f"Invalid task_id format: {str(e)}",
                "status": 400
            }
        )

    except (DBAPIError, OperationalError) as e:
        # Handle database errors with RFC 7807 format
        raise HTTPException(
            status_code=503,
            detail={
                "type": "service-unavailable",
                "title": "Service Unavailable",
                "detail": "Database temporarily unavailable",
                "status": 503
            }
        )
