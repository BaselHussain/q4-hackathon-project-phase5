"""
Dependency injection functions for FastAPI endpoints.

This module provides reusable dependencies for user validation and database access.
"""
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User


async def validate_user_id(x_user_id: Annotated[str | None, Header()] = None) -> UUID:
    """
    Dependency to validate X-User-ID header.

    Extracts the X-User-ID header and validates it's a valid UUID format.
    Returns 400 RFC 7807 error if missing or invalid.

    Args:
        x_user_id: User ID from X-User-ID header

    Returns:
        UUID: Validated user ID

    Raises:
        HTTPException: 400 error if header is missing or invalid UUID format
    """
    if x_user_id is None:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "invalid-user-id",
                "title": "Missing User ID",
                "detail": "X-User-ID header is required",
                "status": 400
            }
        )

    try:
        user_uuid = UUID(x_user_id)
        return user_uuid
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "invalid-user-id",
                "title": "Invalid User ID Format",
                "detail": f"X-User-ID must be a valid UUID format, got: {x_user_id}",
                "status": 400
            }
        )


async def get_or_create_user(
    user_id: Annotated[UUID, Depends(validate_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UUID:
    """
    Dependency to get or create a user.

    Checks if user exists in database. If not, creates user with placeholder email.
    Uses INSERT ... ON CONFLICT DO NOTHING for race condition safety.

    Args:
        user_id: Validated user ID from X-User-ID header
        db: Database session

    Returns:
        UUID: The user ID (existing or newly created)
    """
    # Check if user exists
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        return user_id

    # Create user with placeholder email using INSERT ... ON CONFLICT DO NOTHING
    # This handles race conditions where multiple requests try to create the same user
    placeholder_email = f"{user_id}@placeholder.local"

    stmt = insert(User).values(
        id=user_id,
        email=placeholder_email
    ).on_conflict_do_nothing(index_elements=["id"])

    await db.execute(stmt)
    await db.commit()

    return user_id
