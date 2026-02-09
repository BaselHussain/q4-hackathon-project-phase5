"""
Task creation logic for recurring task occurrences.

Calculates next due dates based on recurrence patterns and creates
new tasks via backend API with exponential backoff retry.
"""
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)

# Backend API configuration
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
CREATE_TASK_ENDPOINT = f"{BACKEND_API_URL}/api/tasks"

# Retry configuration (exponential backoff)
MAX_RETRIES = 3
RETRY_DELAYS = [1.0, 5.0, 25.0]  # seconds


def calculate_next_due_date(
    current_due_date: Optional[str],
    pattern: str,
) -> Optional[datetime]:
    """
    Calculate the next due date based on recurrence pattern.

    Args:
        current_due_date: ISO format datetime string of current due date
        pattern: Recurrence pattern (daily/weekly/monthly/yearly)

    Returns:
        Next due date as datetime, or None if pattern is invalid
    """
    if not current_due_date:
        logger.warning("No current due date provided, cannot calculate next")
        return None

    try:
        # Parse ISO format datetime
        current = datetime.fromisoformat(current_due_date.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as e:
        logger.error(f"Invalid date format '{current_due_date}': {e}")
        return None

    # Calculate next occurrence based on pattern
    pattern_lower = pattern.lower()

    if pattern_lower == "daily":
        next_date = current + timedelta(days=1)
    elif pattern_lower == "weekly":
        next_date = current + timedelta(weeks=1)
    elif pattern_lower == "monthly":
        # Use relativedelta for accurate month addition
        next_date = current + relativedelta(months=1)
    elif pattern_lower == "yearly":
        # Use relativedelta for accurate year addition
        next_date = current + relativedelta(years=1)
    else:
        logger.warning(f"Unknown recurrence pattern: {pattern}")
        return None

    logger.info(
        f"Calculated next due date: {current.isoformat()} -> "
        f"{next_date.isoformat()} (pattern={pattern})"
    )
    return next_date


async def create_next_task_occurrence(event_data: dict[str, Any]) -> bool:
    """
    Create next occurrence of a recurring task via backend API.

    Copies task properties from completed task and sets new due date
    based on recurrence pattern. Retries with exponential backoff.

    Args:
        event_data: Event data containing task information

    Returns:
        True if task created successfully, False otherwise
    """
    try:
        # Extract task data from event
        payload = event_data.get("payload", {})
        user_id = event_data.get("user_id")

        if not user_id:
            logger.error("Missing user_id in event data")
            return False

        # Extract task properties
        title = payload.get("title")
        description = payload.get("description")
        priority = payload.get("priority", "medium")
        tags = payload.get("tags")
        recurring_pattern = payload.get("recurring_pattern")
        due_date_str = payload.get("due_date")

        if not title:
            logger.error("Missing title in event payload")
            return False

        # Calculate next due date
        next_due_date = calculate_next_due_date(due_date_str, recurring_pattern)

        if not next_due_date:
            logger.error("Failed to calculate next due date")
            return False

        # Build task creation payload
        task_data = {
            "title": title,
            "description": description,
            "priority": priority,
            "tags": tags,
            "recurrence": recurring_pattern,
            "due_date": next_due_date.isoformat(),
        }

        # Remove None values
        task_data = {k: v for k, v in task_data.items() if v is not None}

        logger.info(
            f"Creating next task occurrence for user {user_id}: {task_data}"
        )

        # Retry with exponential backoff
        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # Note: In production, need to include authentication
                    # headers with service account or user token
                    headers = {
                        "Content-Type": "application/json",
                        "X-User-ID": user_id,  # Simplified auth for now
                    }

                    response = await client.post(
                        CREATE_TASK_ENDPOINT,
                        json=task_data,
                        headers=headers,
                    )

                    if response.status_code == 201:
                        created_task = response.json()
                        logger.info(
                            f"Successfully created task {created_task.get('id')} "
                            f"(attempt {attempt + 1}/{MAX_RETRIES})"
                        )
                        return True

                    elif response.status_code in (400, 422):
                        # Client error, don't retry
                        logger.error(
                            f"Client error creating task: "
                            f"HTTP {response.status_code} - {response.text}"
                        )
                        return False

                    else:
                        # Server error, retry with backoff
                        logger.warning(
                            f"Server error creating task "
                            f"(attempt {attempt + 1}/{MAX_RETRIES}): "
                            f"HTTP {response.status_code} - {response.text}"
                        )

            except httpx.ConnectError as e:
                logger.warning(
                    f"Connection error (attempt {attempt + 1}/{MAX_RETRIES}): {e}"
                )
            except httpx.TimeoutException as e:
                logger.warning(
                    f"Timeout error (attempt {attempt + 1}/{MAX_RETRIES}): {e}"
                )
            except Exception as e:
                logger.error(
                    f"Unexpected error (attempt {attempt + 1}/{MAX_RETRIES}): {e}",
                    exc_info=True,
                )

            # Wait before retrying (exponential backoff)
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                logger.info(f"Retrying in {delay} seconds...")
                await httpx.AsyncClient().aclose()  # Clean up
                import asyncio
                await asyncio.sleep(delay)

        logger.error(
            f"Failed to create task after {MAX_RETRIES} attempts"
        )
        return False

    except Exception as e:
        logger.error(
            f"Unexpected error in create_next_task_occurrence: {e}",
            exc_info=True,
        )
        return False
