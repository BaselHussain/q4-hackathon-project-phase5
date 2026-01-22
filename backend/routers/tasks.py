"""
Tasks router for Task Management API.

This module implements endpoints for task operations including listing,
creating, updating, and deleting tasks.
"""
from typing import List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_or_create_user, validate_user_id
from models import Task, TaskStatus
from schemas import TaskCreate, TaskResponse, TaskUpdate

# Create router with prefix and tags
router = APIRouter(
    prefix="/api/tasks",
    tags=["tasks"]
)


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    user_id: UUID = Depends(validate_user_id),
    db: AsyncSession = Depends(get_db)
) -> List[TaskResponse]:
    """
    Get all tasks for the authenticated user.

    Retrieves all tasks belonging to the user identified by the X-User-ID header.
    Tasks are returned in descending order by creation date (newest first).

    Args:
        user_id: User ID from X-User-ID header (validated by validate_user_id dependency)
        db: Database session

    Returns:
        List[TaskResponse]: List of tasks (empty list if user has no tasks)

    Raises:
        HTTPException: 503 error if database is temporarily unavailable
    """
    try:
        # Query tasks filtered by user_id, ordered by created_at DESC
        stmt = (
            select(Task)
            .where(Task.user_id == user_id)
            .order_by(Task.created_at.desc())
        )

        result = await db.execute(stmt)
        tasks = result.scalars().all()

        # Return empty list if no tasks found (happens naturally)
        return [TaskResponse.model_validate(task) for task in tasks]

    except (DBAPIError, OperationalError) as e:
        # Handle database connection failures with RFC 7807 error
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
    user_id: UUID = Depends(validate_user_id),
    _: UUID = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db)
) -> TaskResponse:
    """
    Create a new task for the authenticated user.

    Creates a new task with the provided title and optional description.
    The task is automatically assigned to the user identified by the X-User-ID header.
    If the user doesn't exist, they are automatically created.

    Args:
        task_data: Task creation data (title and optional description)
        user_id: User ID from X-User-ID header (validated by validate_user_id dependency)
        _: Ensures user exists via get_or_create_user dependency
        db: Database session

    Returns:
        TaskResponse: The newly created task with status="pending" and 201 Created status

    Raises:
        HTTPException: 400 error if validation fails (title/description constraints)
        HTTPException: 503 error if database is temporarily unavailable
    """
    try:
        # T028: Generate UUID for new task
        task_id = uuid4()

        # T027-T030: Create new task instance with all required fields
        new_task = Task(
            id=task_id,
            user_id=user_id,
            title=task_data.title,
            description=task_data.description,
            status=TaskStatus.PENDING  # T029: Set default status="pending"
        )

        # T034: Save to database and return with 201 Created
        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)

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
    user_id: UUID = Depends(validate_user_id),
    db: AsyncSession = Depends(get_db)
) -> TaskResponse:
    """
    Toggle task completion status between pending and completed.

    Marks a pending task as completed, or a completed task as pending.
    Only the task owner can toggle completion status.

    Args:
        task_id: UUID of the task to toggle
        user_id: User ID from X-User-ID header (validated by validate_user_id dependency)
        db: Database session

    Returns:
        TaskResponse: The updated task with toggled status and 200 OK status

    Raises:
        HTTPException: 400 error if task_id is invalid UUID format
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
    user_id: UUID = Depends(validate_user_id),
    db: AsyncSession = Depends(get_db)
) -> TaskResponse:
    """
    Update task title and/or description.

    Updates one or more fields of an existing task. At least one field must be provided.
    Only the task owner can update the task. Status and created_at are preserved.

    Args:
        task_id: UUID of the task to update
        task_data: Task update data (title and/or description)
        user_id: User ID from X-User-ID header (validated by validate_user_id dependency)
        db: Database session

    Returns:
        TaskResponse: The updated task with 200 OK status

    Raises:
        HTTPException: 400 error if no fields provided or validation fails
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

        # T048: Update only provided fields (title and/or description)
        # T051: Validation of at least one field is handled by TaskUpdate schema
        if task_data.title is not None:
            task.title = task_data.title
        if task_data.description is not None:
            task.description = task_data.description

        # T049: Preserve status and created_at fields (not modified)
        # T050: Update updated_at timestamp (handled automatically by onupdate trigger)
        await db.commit()
        await db.refresh(task)

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
    user_id: UUID = Depends(validate_user_id),
    db: AsyncSession = Depends(get_db)
) -> TaskResponse:
    """
    Get a single task by ID.

    Retrieves complete details of a specific task. Only the task owner can view the task.

    Args:
        task_id: UUID of the task to retrieve
        user_id: User ID from X-User-ID header (validated by validate_user_id dependency)
        db: Database session

    Returns:
        TaskResponse: The task with all fields and 200 OK status

    Raises:
        HTTPException: 400 error if task_id is invalid UUID format
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
    user_id: UUID = Depends(validate_user_id),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a task permanently.

    Removes a task from the database. Only the task owner can delete the task.
    This operation cannot be undone.

    Args:
        task_id: UUID of the task to delete
        user_id: User ID from X-User-ID header (validated by validate_user_id dependency)
        db: Database session

    Returns:
        None: 204 No Content on successful deletion

    Raises:
        HTTPException: 400 error if task_id is invalid UUID format
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

        # T063: Delete task from database
        await db.delete(task)
        await db.commit()

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
