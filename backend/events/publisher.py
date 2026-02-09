"""
Event publisher for Dapr Pub/Sub HTTP API.

Publishes CloudEvents-compliant events to Oracle Streaming Service via Dapr sidecar.
Uses httpx async client for non-blocking HTTP calls.

All events include:
- Idempotency keys (UUID v4) to prevent duplicate processing
- Sequence numbers for event ordering per task
- CloudEvents 1.0 envelope for interoperability
"""
import logging
import os
from datetime import datetime
from typing import Any
from uuid import UUID

import httpx

from events.schemas import (
    CloudEvent,
    TaskEventPayload,
    TaskEventType,
    ReminderEventType,
)

logger = logging.getLogger(__name__)

# Dapr sidecar HTTP endpoint
DAPR_HTTP_PORT = os.getenv("DAPR_HTTP_PORT", "3500")
DAPR_BASE_URL = f"http://localhost:{DAPR_HTTP_PORT}"
PUBSUB_NAME = "pubsub"

# Topics
TOPIC_TASK_EVENTS = "task-events"
TOPIC_REMINDERS = "reminders"
TOPIC_TASK_UPDATES = "task-updates"

# In-memory sequence counter (per-task, resets on restart)
# In production, use Dapr State Store for persistence
_sequence_counters: dict[str, int] = {}


def _get_next_sequence(task_id: str) -> int:
    """Get next monotonically increasing sequence number for a task."""
    current = _sequence_counters.get(task_id, 0)
    next_seq = current + 1
    _sequence_counters[task_id] = next_seq
    return next_seq


async def publish_event(topic: str, event: CloudEvent) -> bool:
    """
    Publish a CloudEvent to a Dapr Pub/Sub topic.

    Args:
        topic: The topic name to publish to
        event: The CloudEvent to publish

    Returns:
        True if published successfully, False otherwise
    """
    url = f"{DAPR_BASE_URL}/v1.0/publish/{PUBSUB_NAME}/{topic}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                json=event.model_dump(),
                headers={"Content-Type": "application/cloudevents+json"},
            )
            response.raise_for_status()
            logger.info(
                f"Published event {event.type} to {topic} "
                f"(id={event.id})"
            )
            return True

    except httpx.ConnectError:
        logger.warning(
            f"Dapr sidecar not available at {DAPR_BASE_URL}. "
            f"Event {event.type} (id={event.id}) not published to {topic}. "
            f"This is expected in development without Dapr running."
        )
        return False

    except httpx.HTTPStatusError as e:
        logger.error(
            f"Failed to publish event {event.type} to {topic}: "
            f"HTTP {e.response.status_code} - {e.response.text}"
        )
        return False

    except Exception as e:
        logger.error(
            f"Unexpected error publishing event {event.type} to {topic}: {e}"
        )
        return False


async def publish_task_event(
    event_type: TaskEventType,
    task_id: UUID,
    user_id: UUID,
    payload: TaskEventPayload,
) -> bool:
    """
    Publish a task lifecycle event to the task-events topic.

    Args:
        event_type: The type of task event
        task_id: The task ID
        user_id: The user who performed the action
        payload: The task event payload

    Returns:
        True if published successfully, False otherwise
    """
    sequence = _get_next_sequence(str(task_id))
    event = CloudEvent.create_task_event(
        event_type=event_type,
        task_id=task_id,
        user_id=user_id,
        sequence=sequence,
        payload=payload,
    )
    return await publish_event(TOPIC_TASK_EVENTS, event)


async def publish_reminder_event(
    event_type: ReminderEventType,
    task_id: UUID,
    user_id: UUID,
    due_date: datetime,
    reminder_time: datetime,
    notification_channels: list[str] | None = None,
    user_email: str | None = None,
    device_tokens: list[str] | None = None,
) -> bool:
    """
    Publish a reminder event to the reminders topic.

    Args:
        event_type: SCHEDULE or CANCEL
        task_id: The task ID
        user_id: The user to notify
        due_date: The task due date
        reminder_time: When to send the reminder
        notification_channels: List of channels (email, push)
        user_email: User's email for email notifications
        device_tokens: FCM tokens for push notifications

    Returns:
        True if published successfully, False otherwise
    """
    event = CloudEvent.create_reminder_event(
        event_type=event_type,
        task_id=task_id,
        user_id=user_id,
        due_date=due_date,
        reminder_time=reminder_time,
        notification_channels=notification_channels,
        user_email=user_email,
        device_tokens=device_tokens,
    )
    return await publish_event(TOPIC_REMINDERS, event)


async def publish_sync_event(
    task_id: UUID,
    user_id: UUID,
    changed_fields: dict[str, Any],
) -> bool:
    """
    Publish a task update event to the task-updates topic for real-time sync.

    Args:
        task_id: The task ID
        user_id: The user who owns the task
        changed_fields: Dictionary of field names to new values

    Returns:
        True if published successfully, False otherwise
    """
    sequence = _get_next_sequence(str(task_id))
    event = CloudEvent.create_sync_event(
        task_id=task_id,
        user_id=user_id,
        sequence=sequence,
        changed_fields=changed_fields,
    )
    return await publish_event(TOPIC_TASK_UPDATES, event)
