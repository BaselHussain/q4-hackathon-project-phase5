"""
Event consumer for reminder events.

Handles reminder.schedule and reminder.cancel events from Dapr Pub/Sub.
Implements idempotency using processed event IDs tracking.
"""
import logging
from typing import Any, Set

from scheduler import cancel_reminder, schedule_reminder

logger = logging.getLogger(__name__)

# In-memory set for tracking processed event IDs (idempotency)
# In production, use Dapr State Store or Redis for distributed idempotency
processed_event_ids: Set[str] = set()


async def handle_reminder_event(event: dict[str, Any]) -> None:
    """
    Process reminder events from Dapr Pub/Sub.

    Event types:
    - com.todo.reminder.schedule: Schedule a new reminder via Dapr Jobs API
    - com.todo.reminder.cancel: Cancel an existing reminder via Dapr Jobs API

    Implements idempotency check to prevent duplicate processing.

    Args:
        event: CloudEvent dictionary with type, id, and data fields
    """
    event_id = event.get("id")
    event_type = event.get("type")
    event_data = event.get("data", {})

    if not event_id:
        logger.error("Event missing 'id' field, cannot ensure idempotency")
        return

    # Idempotency check
    if event_id in processed_event_ids:
        logger.info(f"Event {event_id} already processed, skipping")
        return

    try:
        logger.info(f"Processing event {event_id} of type {event_type}")

        if event_type == "com.todo.reminder.schedule":
            await handle_schedule_event(event_data)
        elif event_type == "com.todo.reminder.cancel":
            await handle_cancel_event(event_data)
        else:
            logger.warning(f"Unknown event type: {event_type}")
            return

        # Mark event as processed
        processed_event_ids.add(event_id)
        logger.info(f"Event {event_id} processed successfully")

    except Exception as e:
        logger.error(f"Error processing event {event_id}: {str(e)}", exc_info=True)
        # Re-raise to trigger retry mechanism
        raise


async def handle_schedule_event(data: dict[str, Any]) -> None:
    """
    Handle reminder.schedule event.

    Schedules a reminder using Dapr Jobs API.

    Args:
        data: Event data containing task_id, user_id, due_date, reminder_time, etc.
    """
    task_id = data.get("task_id")
    user_id = data.get("user_id")
    reminder_time = data.get("reminder_time")
    due_date = data.get("due_date")
    user_email = data.get("user_email")
    device_tokens = data.get("device_tokens", [])
    notification_channels = data.get("notification_channels", ["email", "push"])

    if not task_id or not reminder_time:
        logger.error(f"Schedule event missing required fields: task_id={task_id}, reminder_time={reminder_time}")
        return

    logger.info(f"Scheduling reminder for task_id={task_id} at {reminder_time}")

    # Prepare task data for job payload
    task_data = {
        "task_id": task_id,
        "user_id": user_id,
        "due_date": due_date,
        "user_email": user_email,
        "device_tokens": device_tokens,
        "notification_channels": notification_channels
    }

    # Schedule reminder via Dapr Jobs API
    await schedule_reminder(task_id, reminder_time, task_data)


async def handle_cancel_event(data: dict[str, Any]) -> None:
    """
    Handle reminder.cancel event.

    Cancels a scheduled reminder using Dapr Jobs API.

    Args:
        data: Event data containing task_id
    """
    task_id = data.get("task_id")

    if not task_id:
        logger.error("Cancel event missing task_id field")
        return

    logger.info(f"Cancelling reminder for task_id={task_id}")

    # Cancel reminder via Dapr Jobs API
    await cancel_reminder(task_id)
