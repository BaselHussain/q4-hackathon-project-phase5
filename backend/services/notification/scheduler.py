"""
Dapr Jobs API integration for scheduling task reminders.

Uses Dapr Jobs API to schedule one-time reminder notifications.
Stores reminder metadata in Dapr State Store for tracking.
"""
import logging
import os
from datetime import datetime
from typing import Any

import httpx

from notifiers.email import send_email
from notifiers.push import send_push

logger = logging.getLogger(__name__)

# Environment configuration
DAPR_HTTP_PORT = os.getenv("DAPR_HTTP_PORT", "3500")
DAPR_BASE_URL = f"http://localhost:{DAPR_HTTP_PORT}"
STATE_STORE_NAME = "statestore"


async def schedule_reminder(task_id: str, reminder_time: str, task_data: dict[str, Any]) -> None:
    """
    Schedule a reminder using Dapr Jobs API.

    Creates a one-time job that triggers at the specified reminder_time.
    When triggered, Dapr sends POST request to /jobs/reminder-{task_id}.

    Args:
        task_id: Unique task identifier
        reminder_time: ISO 8601 timestamp when reminder should trigger (e.g., "2026-02-10T09:45:00Z")
        task_data: Task metadata to include in job payload (user_id, due_date, email, etc.)
    """
    job_name = f"reminder-{task_id}"

    # Dapr Jobs API payload
    job_payload = {
        "schedule": reminder_time,  # ISO 8601 timestamp
        "data": task_data,  # Custom payload passed to callback
        "repeats": 0  # One-time job
    }

    try:
        logger.info(f"Scheduling job {job_name} at {reminder_time}")

        async with httpx.AsyncClient() as client:
            # POST to Dapr Jobs API
            response = await client.post(
                f"{DAPR_BASE_URL}/v1.0-alpha1/jobs/{job_name}",
                json=job_payload,
                timeout=10.0
            )
            response.raise_for_status()

        logger.info(f"Job {job_name} scheduled successfully")

        # Store reminder metadata in Dapr State Store
        await save_reminder_state(task_id, {
            "task_id": task_id,
            "reminder_time": reminder_time,
            "scheduled_at": datetime.utcnow().isoformat(),
            "status": "scheduled",
            **task_data
        })

    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to schedule job {job_name}: HTTP {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Error scheduling job {job_name}: {str(e)}", exc_info=True)
        raise


async def cancel_reminder(task_id: str) -> None:
    """
    Cancel a scheduled reminder using Dapr Jobs API.

    Deletes the job if it exists and hasn't triggered yet.

    Args:
        task_id: Unique task identifier
    """
    job_name = f"reminder-{task_id}"

    try:
        logger.info(f"Cancelling job {job_name}")

        async with httpx.AsyncClient() as client:
            # DELETE from Dapr Jobs API
            response = await client.delete(
                f"{DAPR_BASE_URL}/v1.0-alpha1/jobs/{job_name}",
                timeout=10.0
            )

            # 204 = successfully deleted, 404 = job doesn't exist (already triggered or never created)
            if response.status_code == 204:
                logger.info(f"Job {job_name} cancelled successfully")
            elif response.status_code == 404:
                logger.warning(f"Job {job_name} not found (may have already triggered)")
            else:
                response.raise_for_status()

        # Update reminder state
        await save_reminder_state(task_id, {
            "task_id": task_id,
            "cancelled_at": datetime.utcnow().isoformat(),
            "status": "cancelled"
        })

    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to cancel job {job_name}: HTTP {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Error cancelling job {job_name}: {str(e)}", exc_info=True)
        raise


async def save_reminder_state(task_id: str, state_data: dict[str, Any]) -> None:
    """
    Save reminder metadata to Dapr State Store.

    Uses key pattern: reminder:{task_id}

    Args:
        task_id: Task identifier
        state_data: Reminder metadata to persist
    """
    state_key = f"reminder:{task_id}"

    try:
        async with httpx.AsyncClient() as client:
            # POST to Dapr State Store API
            response = await client.post(
                f"{DAPR_BASE_URL}/v1.0/state/{STATE_STORE_NAME}",
                json=[
                    {
                        "key": state_key,
                        "value": state_data
                    }
                ],
                timeout=5.0
            )
            response.raise_for_status()

        logger.debug(f"Saved reminder state for task_id={task_id}")

    except Exception as e:
        logger.error(f"Error saving reminder state for task_id={task_id}: {str(e)}", exc_info=True)
        # Don't raise - state persistence failure shouldn't block reminder scheduling


async def send_reminder_notification(task_id: str, job_data: dict[str, Any]) -> None:
    """
    Send reminder notification when Dapr Job triggers.

    Called by /jobs/reminder-{task_id} endpoint when reminder is due.
    Sends notifications via configured channels (email, push).

    Args:
        task_id: Task identifier
        job_data: Job payload containing notification details
    """
    user_email = job_data.get("user_email")
    device_tokens = job_data.get("device_tokens", [])
    notification_channels = job_data.get("notification_channels", ["email", "push"])
    due_date = job_data.get("due_date")

    logger.info(f"Sending reminder notification for task_id={task_id}, channels={notification_channels}")

    # Prepare notification content
    subject = "Task Reminder"
    body = f"Your task is due at {due_date}. Don't forget to complete it!"
    title = "Task Reminder"

    success_count = 0
    total_count = 0

    # Send email notification
    if "email" in notification_channels and user_email:
        total_count += 1
        if await send_email(user_email, subject, body):
            success_count += 1
            logger.info(f"Email notification sent to {user_email}")
        else:
            logger.error(f"Failed to send email notification to {user_email}")

    # Send push notifications
    if "push" in notification_channels and device_tokens:
        for token in device_tokens:
            total_count += 1
            if await send_push(token, title, body):
                success_count += 1
                logger.info(f"Push notification sent to device token {token[:10]}...")
            else:
                logger.error(f"Failed to send push notification to device token {token[:10]}...")

    # Update reminder state
    await save_reminder_state(task_id, {
        "task_id": task_id,
        "sent_at": datetime.utcnow().isoformat(),
        "status": "sent",
        "success_count": success_count,
        "total_count": total_count
    })

    logger.info(f"Reminder notification sent for task_id={task_id}: {success_count}/{total_count} successful")
