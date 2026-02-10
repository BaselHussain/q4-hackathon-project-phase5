"""
E2E Test: Recurring Task Flow
Tests: Complete recurring task -> new task instance created -> event published

Validates that completing a recurring task triggers the recurring-task service
to automatically create the next occurrence.
"""
import asyncio
from typing import Dict

import httpx
import pytest

from .conftest import API_BASE_URL


@pytest.mark.asyncio
class TestRecurringTaskFlow:
    """Test the recurring task auto-creation flow."""

    async def test_complete_recurring_task_creates_next_occurrence(
        self, http_client: httpx.AsyncClient, auth_headers: Dict[str, str]
    ):
        """Completing a recurring task triggers creation of next occurrence."""
        user_id = auth_headers["user_id"]
        headers = {"Authorization": auth_headers["Authorization"]}

        # Create a recurring task
        resp = await http_client.post(
            f"/api/{user_id}/tasks",
            json={
                "title": "Recurring E2E Test",
                "description": "Should auto-create next occurrence",
                "recurrence": "daily",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        task = resp.json()
        original_task_id = task["id"]

        # Complete the recurring task
        complete_resp = await http_client.patch(
            f"/api/{user_id}/tasks/{original_task_id}/complete",
            headers=headers,
        )
        assert complete_resp.status_code == 200
        assert complete_resp.json()["status"] == "completed"

        # Wait for recurring-task service to process the event
        await asyncio.sleep(10)

        # Check that a new task was created with same title
        list_resp = await http_client.get(
            f"/api/{user_id}/tasks?status=pending&search=Recurring E2E Test",
            headers=headers,
        )
        assert list_resp.status_code == 200
        pending_tasks = list_resp.json()

        # There should be a new pending task with the same title
        matching = [t for t in pending_tasks if "Recurring E2E Test" in t["title"] and t["id"] != original_task_id]

        # Cleanup all created tasks
        for t in matching:
            await http_client.delete(f"/api/{user_id}/tasks/{t['id']}", headers=headers)
        await http_client.delete(f"/api/{user_id}/tasks/{original_task_id}", headers=headers)

        assert len(matching) >= 1, "Recurring task service should have created a new task instance"

    async def test_recurring_task_service_health(
        self, http_client: httpx.AsyncClient
    ):
        """Recurring task service health check passes."""
        try:
            resp = await http_client.get("http://localhost:8001/health")
            assert resp.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Recurring task service not reachable at localhost:8001")

    async def test_non_recurring_task_does_not_create_occurrence(
        self, http_client: httpx.AsyncClient, auth_headers: Dict[str, str]
    ):
        """Completing a non-recurring task does NOT create a new occurrence."""
        user_id = auth_headers["user_id"]
        headers = {"Authorization": auth_headers["Authorization"]}

        # Create a non-recurring task
        resp = await http_client.post(
            f"/api/{user_id}/tasks",
            json={"title": "Non-Recurring E2E Test"},
            headers=headers,
        )
        assert resp.status_code == 201
        task_id = resp.json()["id"]

        # Complete it
        await http_client.patch(f"/api/{user_id}/tasks/{task_id}/complete", headers=headers)

        # Wait briefly
        await asyncio.sleep(5)

        # Check no new pending task with same title
        list_resp = await http_client.get(
            f"/api/{user_id}/tasks?status=pending&search=Non-Recurring E2E Test",
            headers=headers,
        )
        matching = [t for t in list_resp.json() if t["id"] != task_id]
        assert len(matching) == 0, "Non-recurring task should not create new occurrences"

        # Cleanup
        await http_client.delete(f"/api/{user_id}/tasks/{task_id}", headers=headers)
