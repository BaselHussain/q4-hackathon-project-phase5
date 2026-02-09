"""
Event consumer for processing task lifecycle events.

Handles task.completed events for recurring tasks by delegating
to task_creator to generate next occurrences.
"""
import logging
from typing import Any

from task_creator import create_next_task_occurrence

logger = logging.getLogger(__name__)

# In-memory idempotency tracking
# In production, use Dapr State Store or Redis for persistence
_processed_events: set[str] = set()


async def handle_task_event(event: dict[str, Any]) -> bool:
    """
    Process a task lifecycle event from the task-events topic.

    Checks for idempotency, validates event type, and creates next
    occurrence for recurring tasks when completed.

    Args:
        event: CloudEvent containing task lifecycle data

    Returns:
        True if event processed successfully, False otherwise
    """
    try:
        # Extract CloudEvent fields
        event_id = event.get("id")
        event_type = event.get("type")
        event_data = event.get("data", {})

        if not event_id:
            logger.error("Event missing required 'id' field")
            return False

        # Idempotency check
        if event_id in _processed_events:
            logger.info(
                f"Event {event_id} already processed, skipping (idempotent)"
            )
            return True

        # Only process task.completed events
        if event_type != "com.todo.task.completed":
            logger.debug(
                f"Ignoring event type {event_type}, not a completion event"
            )
            _processed_events.add(event_id)
            return True

        # Extract task data
        task_id = event_data.get("task_id")
        payload = event_data.get("payload", {})
        recurring_pattern = payload.get("recurring_pattern", "none")

        logger.info(
            f"Processing task.completed event: "
            f"task_id={task_id}, pattern={recurring_pattern}"
        )

        # Check if task is recurring
        if recurring_pattern == "none":
            logger.debug(
                f"Task {task_id} is not recurring, no action needed"
            )
            _processed_events.add(event_id)
            return True

        # Create next occurrence
        success = await create_next_task_occurrence(event_data)

        if success:
            logger.info(
                f"Successfully created next occurrence for task {task_id}"
            )
            _processed_events.add(event_id)
            return True
        else:
            logger.error(
                f"Failed to create next occurrence for task {task_id}"
            )
            return False

    except KeyError as e:
        logger.error(f"Missing required field in event: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(
            f"Unexpected error processing event: {e}",
            exc_info=True,
        )
        return False
