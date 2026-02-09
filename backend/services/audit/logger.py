"""
Audit log writer with idempotency and retry logic.

This module provides functions to write audit log entries to the database
with proper error handling, retry logic, and idempotency guarantees.
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Optional
from uuid import UUID

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Load environment variables from .env file
load_dotenv()

from src.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Create async engine for audit service
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def write_audit_log(
    event_id: UUID,
    timestamp: datetime,
    user_id: UUID,
    event_type: str,
    task_id: Optional[UUID],
    payload: dict
) -> bool:
    """
    Write an audit log entry to the database with idempotency and retry logic.

    Implements:
    - Idempotency: Uses event_id as unique constraint to prevent duplicates
    - Retry logic: 3 attempts with exponential backoff (1s, 5s, 25s)
    - Error handling: Logs failures and returns success/failure status

    Args:
        event_id: Unique event identifier for idempotency
        timestamp: When the event occurred
        user_id: User who triggered the event
        event_type: Type of event (e.g., 'task.created')
        task_id: Related task ID (can be None)
        payload: Event-specific data as dictionary

    Returns:
        bool: True if successfully written or already exists, False on failure

    Raises:
        No exceptions raised - all errors are logged and handled internally
    """
    max_retries = 3
    retry_delays = [1, 5, 25]  # Exponential backoff: 1s, 5s, 25s

    for attempt in range(max_retries):
        try:
            async with AsyncSessionLocal() as session:
                # Check if event already exists (idempotency)
                stmt = select(AuditLog).where(AuditLog.event_id == event_id)
                result = await session.execute(stmt)
                existing_log = result.scalar_one_or_none()

                if existing_log:
                    logger.info(
                        f"Audit log for event_id={event_id} already exists (idempotent), skipping"
                    )
                    return True

                # Create new audit log entry
                audit_log = AuditLog(
                    event_id=event_id,
                    timestamp=timestamp,
                    user_id=user_id,
                    event_type=event_type,
                    task_id=task_id,
                    payload=payload
                )

                session.add(audit_log)
                await session.commit()

                logger.info(
                    f"Successfully wrote audit log: event_id={event_id}, "
                    f"event_type={event_type}, user_id={user_id}"
                )
                return True

        except IntegrityError as e:
            # Duplicate event_id (race condition) - treat as success
            logger.info(
                f"Audit log for event_id={event_id} already exists (race condition), "
                f"treating as success"
            )
            return True

        except OperationalError as e:
            # Database connection or operational error
            if attempt < max_retries - 1:
                delay = retry_delays[attempt]
                logger.warning(
                    f"Database error on attempt {attempt + 1}/{max_retries} "
                    f"for event_id={event_id}: {e}. Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
                continue
            else:
                # Final attempt failed
                logger.error(
                    f"Failed to write audit log after {max_retries} attempts "
                    f"for event_id={event_id}: {e}"
                )
                return False

        except Exception as e:
            # Unexpected error
            logger.error(
                f"Unexpected error writing audit log for event_id={event_id}: {e}",
                exc_info=True
            )
            return False

    # Should never reach here, but just in case
    logger.error(f"Failed to write audit log for event_id={event_id} after all retries")
    return False


async def close_db_connections():
    """
    Close all database connections gracefully.

    Should be called during application shutdown.
    """
    await engine.dispose()
    logger.info("Audit service database connections closed")
