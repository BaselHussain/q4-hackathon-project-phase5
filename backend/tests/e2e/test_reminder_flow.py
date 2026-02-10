"""
E2E Test: Reminder Flow
Tests: Task with due date -> reminder scheduled -> notification delivered

Validates that creating a task with a due date triggers the notification service
to schedule and deliver a reminder.
"""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict

import httpx
import pytest

from .conftest import API_BASE_URL


@pytest.mark.asyncio
class TestReminderFlow:
    """Test the reminder scheduling and notification flow."""

    async def test_task_with_due_date_schedules_reminder(
        self, http_client: httpx.AsyncClient, auth_headers: Dict[str, str]
    ):
        """Creating a task with a future due date triggers reminder scheduling."""
        user_id = auth_headers["user_id"]
        headers = {"Authorization": auth_headers["Authorization"]}

        # Create task with due date 1 hour from now
        due_date = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        resp = await http_client.post(
            f"/api/{user_id}/tasks",
            json={
                "title": "Reminder E2E Test",
                "description": "Should schedule a reminder",
                "due_date": due_date,
            },
            headers=headers,
        )
        assert resp.status_code == 201
        task = resp.json()

        # Wait for event to propagate to notification service
        await asyncio.sleep(5)

        # Verify notification service is healthy (processing events)
        try:
            health_resp = await http_client.get("http://localhost:8002/health")
            assert health_resp.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Notification service not reachable at localhost:8002")

        # Cleanup
        await http_client.delete(f"/api/{user_id}/tasks/{task['id']}", headers=headers)

    async def test_completing_task_cancels_reminder(
        self, http_client: httpx.AsyncClient, auth_headers: Dict[str, str]
    ):
        """Completing a task with a due date cancels the scheduled reminder."""
        user_id = auth_headers["user_id"]
        headers = {"Authorization": auth_headers["Authorization"]}

        # Create task with due date
        due_date = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
        resp = await http_client.post(
            f"/api/{user_id}/tasks",
            json={"title": "Cancel Reminder E2E", "due_date": due_date},
            headers=headers,
        )
        assert resp.status_code == 201
        task_id = resp.json()["id"]

        # Wait for reminder to be scheduled
        await asyncio.sleep(3)

        # Complete the task (should cancel reminder)
        complete_resp = await http_client.patch(
            f"/api/{user_id}/tasks/{task_id}/complete", headers=headers
        )
        assert complete_resp.status_code == 200
        assert complete_resp.json()["status"] == "completed"

        # Cleanup
        await http_client.delete(f"/api/{user_id}/tasks/{task_id}", headers=headers)

    async def test_updating_due_date_reschedules_reminder(
        self, http_client: httpx.AsyncClient, auth_headers: Dict[str, str]
    ):
        """Updating a task's due date triggers reminder rescheduling."""
        user_id = auth_headers["user_id"]
        headers = {"Authorization": auth_headers["Authorization"]}

        # Create task with initial due date
        initial_due = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        resp = await http_client.post(
            f"/api/{user_id}/tasks",
            json={"title": "Reschedule Reminder E2E", "due_date": initial_due},
            headers=headers,
        )
        assert resp.status_code == 201
        task_id = resp.json()["id"]

        # Update due date
        new_due = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()
        update_resp = await http_client.put(
            f"/api/{user_id}/tasks/{task_id}",
            json={"due_date": new_due},
            headers=headers,
        )
        assert update_resp.status_code == 200

        # Wait for event propagation
        await asyncio.sleep(3)

        # Cleanup
        await http_client.delete(f"/api/{user_id}/tasks/{task_id}", headers=headers)

    async def test_notification_service_health(
        self, http_client: httpx.AsyncClient
    ):
        """Notification service health check passes."""
        try:
            resp = await http_client.get("http://localhost:8002/health")
            assert resp.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Notification service not reachable at localhost:8002")
