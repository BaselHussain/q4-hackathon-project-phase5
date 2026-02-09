"""
Kafka event consumer for task updates.

This module handles task update events from Kafka via Dapr Pub/Sub
and broadcasts them to connected WebSocket clients.
"""
import logging
from typing import Dict, Any

from websocket import ConnectionManager


logger = logging.getLogger(__name__)


async def handle_task_update(event: Dict[str, Any], manager: ConnectionManager) -> None:
    """
    Process a task update event and broadcast to relevant user.

    Args:
        event: Task update event dictionary containing user_id and task data
        manager: ConnectionManager instance for broadcasting

    Event structure:
        {
            "user_id": "uuid-string",
            "task_id": "uuid-string",
            "action": "created|updated|deleted|completed",
            "task": {...}  # Full task data
        }
    """
    try:
        user_id = event.get("user_id")
        action = event.get("action")
        task_id = event.get("task_id")

        if not user_id:
            logger.error(f"Event missing user_id: {event}")
            return

        logger.info(
            f"Processing task update event: action={action}, "
            f"task_id={task_id}, user_id={user_id}"
        )

        # Broadcast to all user's WebSocket connections
        await manager.broadcast_to_user(user_id, event)

        logger.info(f"Successfully broadcasted event to user {user_id}")

    except Exception as e:
        logger.error(f"Error handling task update event: {e}", exc_info=True)
