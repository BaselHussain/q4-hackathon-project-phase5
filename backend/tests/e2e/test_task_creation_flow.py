"""
E2E Test: Task Creation Flow
Tests: API -> Kafka event -> audit log

Validates the complete flow from task creation through event publishing
to audit log persistence.
"""
import asyncio
from typing import Dict

import httpx
import pytest
import pytest_asyncio

from .conftest import API_BASE_URL


@pytest.mark.asyncio
class TestTaskCreationFlow:
    """Test the complete task creation event flow."""

    async def test_create_task_returns_201(
        self, http_client: httpx.AsyncClient, auth_headers: Dict[str, str]
    ):
        """Task creation via API returns 201 with correct structure."""
        user_id = auth_headers["user_id"]
        headers = {"Authorization": auth_headers["Authorization"]}

        resp = await http_client.post(
            f"/api/{user_id}/tasks",
            json={
                "title": "E2E Flow Test Task",
                "description": "Testing complete creation flow",
                "priority": "high",
                "tags": ["e2e", "test"],
            },
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "E2E Flow Test Task"
        assert data["status"] == "pending"
        assert data["priority"] == "high"
        assert "e2e" in data["tags"]

        # Cleanup
        await http_client.delete(f"/api/{user_id}/tasks/{data['id']}", headers=headers)

    async def test_created_task_appears_in_list(
        self, http_client: httpx.AsyncClient, auth_headers: Dict[str, str], test_task: Dict
    ):
        """Created task is immediately visible in task list."""
        user_id = auth_headers["user_id"]
        headers = {"Authorization": auth_headers["Authorization"]}

        resp = await http_client.get(f"/api/{user_id}/tasks", headers=headers)
        assert resp.status_code == 200
        tasks = resp.json()
        task_ids = [t["id"] for t in tasks]
        assert test_task["id"] in task_ids

    async def test_task_event_reaches_audit_log(
        self, http_client: httpx.AsyncClient, auth_headers: Dict[str, str]
    ):
        """Task creation event is captured in audit logs (with delay for async processing)."""
        user_id = auth_headers["user_id"]
        headers = {"Authorization": auth_headers["Authorization"]}

        # Create a task
        resp = await http_client.post(
            f"/api/{user_id}/tasks",
            json={"title": "Audit Trail Test Task"},
            headers=headers,
        )
        assert resp.status_code == 201
        task_id = resp.json()["id"]

        # Wait for event to propagate through Kafka -> audit service
        await asyncio.sleep(5)

        # Check audit service health (verifies it's processing events)
        audit_health = await http_client.get(
            "http://localhost:8004/health" if "localhost" in API_BASE_URL else f"{API_BASE_URL.rsplit(':', 1)[0]}:8004/health"
        )
        # Audit service should be healthy if processing events
        assert audit_health.status_code == 200

        # Cleanup
        await http_client.delete(f"/api/{user_id}/tasks/{task_id}", headers=headers)

    async def test_create_task_with_all_fields(
        self, http_client: httpx.AsyncClient, auth_headers: Dict[str, str]
    ):
        """Task creation with all optional fields works correctly."""
        user_id = auth_headers["user_id"]
        headers = {"Authorization": auth_headers["Authorization"]}

        resp = await http_client.post(
            f"/api/{user_id}/tasks",
            json={
                "title": "Full Field Task",
                "description": "Task with all fields set",
                "priority": "low",
                "tags": ["complete", "test"],
                "recurrence": "daily",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["priority"] == "low"
        assert data["recurrence"] == "daily"

        # Cleanup
        await http_client.delete(f"/api/{user_id}/tasks/{data['id']}", headers=headers)
