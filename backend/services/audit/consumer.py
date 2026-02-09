"""
Event consumer for task events.

This module handles incoming task events from Dapr Pub/Sub and delegates
to the audit logger for persistence.
"""
import logging
from datetime import datetime
from typing import Dict
from uuid import UUID

from .logger import write_audit_log

logger = logging.getLogger(__name__)


async def handle_task_event(event: Dict) -> bool:
    """
    Handle incoming task event and write to audit log.

    Validates event structure, extracts required fields, and delegates to
    the audit logger for persistence with idempotency.

    Expected event structure (Dapr CloudEvent format):
    {
        "id": "event-uuid",
        "source": "task-service",
        "type": "task.created" | "task.updated" | "task.completed" | "task.deleted",
        "datacontenttype": "application/json",
        "time": "2024-01-15T10:30:00Z",
        "data": {
            "task_id": "task-uuid",
            "user_id": "user-uuid",
            "payload": {...}
        }
    }

    Args:
        event: CloudEvent formatted task event

    Returns:
        bool: True if successfully logged, False otherwise

    Raises:
        No exceptions raised - all errors are logged and handled internally
    """
    try:
        # Extract CloudEvent fields
        event_id_str = event.get("id")
        event_type = event.get("type")
        timestamp_str = event.get("time")
        data = event.get("data", {})

        # Validate required fields
        if not event_id_str:
            logger.error("Missing 'id' field in event")
            return False

        if not event_type:
            logger.error(f"Missing 'type' field in event {event_id_str}")
            return False

        if not timestamp_str:
            logger.error(f"Missing 'time' field in event {event_id_str}")
            return False

        # Extract data fields
        task_id_str = data.get("task_id")
        user_id_str = data.get("user_id")
        payload = data.get("payload", {})

        if not user_id_str:
            logger.error(f"Missing 'user_id' in event data for event {event_id_str}")
            return False

        # Parse UUIDs
        try:
            event_id = UUID(event_id_str)
            user_id = UUID(user_id_str)
            task_id = UUID(task_id_str) if task_id_str else None
        except ValueError as e:
            logger.error(
                f"Invalid UUID format in event {event_id_str}: {e}"
            )
            return False

        # Parse timestamp
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except ValueError as e:
            logger.error(
                f"Invalid timestamp format in event {event_id_str}: {e}"
            )
            return False

        # Write to audit log
        logger.info(
            f"Processing event: id={event_id}, type={event_type}, "
            f"user_id={user_id}, task_id={task_id}"
        )

        success = await write_audit_log(
            event_id=event_id,
            timestamp=timestamp,
            user_id=user_id,
            event_type=event_type,
            task_id=task_id,
            payload=payload
        )

        if success:
            logger.info(f"Successfully handled event {event_id}")
        else:
            logger.error(f"Failed to handle event {event_id}")

        return success

    except Exception as e:
        logger.error(
            f"Unexpected error handling event: {e}",
            exc_info=True
        )
        return False
