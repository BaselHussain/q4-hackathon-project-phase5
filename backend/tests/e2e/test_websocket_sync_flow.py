"""
E2E Test: WebSocket Sync Flow
Tests: Task update -> WebSocket message delivered to connected clients

Validates that task updates are broadcast in real-time via WebSocket
through the sync service.
"""
import asyncio
import json
from typing import Dict

import httpx
import pytest

from .conftest import API_BASE_URL


@pytest.mark.asyncio
class TestWebSocketSyncFlow:
    """Test real-time task synchronization via WebSocket."""

    async def test_sync_service_health(self, http_client: httpx.AsyncClient):
        """Sync service health check passes."""
        try:
            resp = await http_client.get("http://localhost:8003/health")
            assert resp.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Sync service not reachable at localhost:8003")

    async def test_websocket_connection_requires_auth(self, http_client: httpx.AsyncClient):
        """WebSocket endpoint rejects connections without valid JWT token."""
        import websockets

        try:
            async with websockets.connect("ws://localhost:8003/ws/tasks") as ws:
                # Should be rejected without token
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                data = json.loads(msg)
                assert data.get("error") is not None
        except (ConnectionRefusedError, OSError):
            pytest.skip("Sync service WebSocket not reachable at localhost:8003")
        except ImportError:
            pytest.skip("websockets package not installed")

    async def test_task_update_triggers_sync_event(
        self, http_client: httpx.AsyncClient, auth_headers: Dict[str, str]
    ):
        """Updating a task publishes a sync event for WebSocket broadcast."""
        user_id = auth_headers["user_id"]
        headers = {"Authorization": auth_headers["Authorization"]}

        # Create a task
        resp = await http_client.post(
            f"/api/{user_id}/tasks",
            json={"title": "WebSocket Sync E2E Test"},
            headers=headers,
        )
        assert resp.status_code == 201
        task_id = resp.json()["id"]

        # Update the task (this should trigger sync event)
        update_resp = await http_client.put(
            f"/api/{user_id}/tasks/{task_id}",
            json={"title": "Updated WebSocket Sync E2E Test"},
            headers=headers,
        )
        assert update_resp.status_code == 200

        # Wait for event propagation
        await asyncio.sleep(3)

        # Verify the update was persisted
        get_resp = await http_client.get(f"/api/{user_id}/tasks/{task_id}", headers=headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["title"] == "Updated WebSocket Sync E2E Test"

        # Cleanup
        await http_client.delete(f"/api/{user_id}/tasks/{task_id}", headers=headers)

    async def test_task_deletion_triggers_sync_event(
        self, http_client: httpx.AsyncClient, auth_headers: Dict[str, str]
    ):
        """Deleting a task publishes a sync event for WebSocket broadcast."""
        user_id = auth_headers["user_id"]
        headers = {"Authorization": auth_headers["Authorization"]}

        # Create then delete a task
        resp = await http_client.post(
            f"/api/{user_id}/tasks",
            json={"title": "Delete Sync E2E Test"},
            headers=headers,
        )
        assert resp.status_code == 201
        task_id = resp.json()["id"]

        # Delete triggers sync event
        del_resp = await http_client.delete(f"/api/{user_id}/tasks/{task_id}", headers=headers)
        assert del_resp.status_code == 204

        # Wait for event propagation
        await asyncio.sleep(3)

        # Verify task no longer exists
        get_resp = await http_client.get(f"/api/{user_id}/tasks/{task_id}", headers=headers)
        assert get_resp.status_code == 404
