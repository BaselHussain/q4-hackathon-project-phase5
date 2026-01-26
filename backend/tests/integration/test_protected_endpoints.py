"""
Integration tests for protected task endpoints.

Tests that task endpoints are properly protected with JWT authentication
and enforce user isolation (users can only access their own tasks).
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import create_access_token


class TestProtectedEndpoints:
    """Integration tests for protected task endpoints (T045)."""

    @pytest.mark.asyncio
    async def test_access_own_tasks_with_valid_token(self, client: AsyncClient, db: AsyncSession):
        """
        Test that users can access their own tasks with valid JWT token.

        Expected: 200 OK with task list.
        """
        # Arrange - Register a user and create a task
        register_payload = {
            "email": "taskowner@example.com",
            "password": "SecurePass123!"
        }
        register_response = await client.post("/api/auth/register", json=register_payload)
        user_id = register_response.json()["user_id"]

        # Login to get token
        login_payload = {
            "email": "taskowner@example.com",
            "password": "SecurePass123!"
        }
        login_response = await client.post("/api/auth/login", json=login_payload)
        token = login_response.json()["access_token"]

        # Create a task
        task_payload = {
            "title": "My Task",
            "description": "Task description"
        }
        create_response = await client.post(
            f"/api/{user_id}/tasks",
            json=task_payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert create_response.status_code == 201

        # Act - Get own tasks with valid token
        response = await client.get(
            f"/api/{user_id}/tasks",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == 200
        tasks = response.json()
        assert isinstance(tasks, list)
        assert len(tasks) >= 1
        assert tasks[0]["title"] == "My Task"

    @pytest.mark.asyncio
    async def test_access_other_user_tasks_forbidden(self, client: AsyncClient, db: AsyncSession):
        """
        Test that users cannot access other users' tasks.

        Expected: 403 Forbidden with RFC 7807 error.
        """
        # Arrange - Create two users
        # User 1
        user1_register = {
            "email": "user1@example.com",
            "password": "SecurePass123!"
        }
        user1_response = await client.post("/api/auth/register", json=user1_register)
        user1_id = user1_response.json()["user_id"]

        user1_login = {
            "email": "user1@example.com",
            "password": "SecurePass123!"
        }
        user1_login_response = await client.post("/api/auth/login", json=user1_login)
        user1_token = user1_login_response.json()["access_token"]

        # User 2
        user2_register = {
            "email": "user2@example.com",
            "password": "SecurePass123!"
        }
        user2_response = await client.post("/api/auth/register", json=user2_register)
        user2_id = user2_response.json()["user_id"]

        # Act - User 1 tries to access User 2's tasks
        response = await client.get(
            f"/api/{user2_id}/tasks",
            headers={"Authorization": f"Bearer {user1_token}"}
        )

        # Assert
        assert response.status_code == 403
        assert response.headers["content-type"] == "application/problem+json"

        error = response.json()
        assert error["type"] == "access-denied"
        assert error["title"] == "Access Denied"
        assert error["status"] == 403
        assert "permission" in error["detail"].lower()

    @pytest.mark.asyncio
    async def test_access_without_token_unauthorized(self, client: AsyncClient, db: AsyncSession):
        """
        Test that requests without JWT token are rejected.

        Expected: 401 Unauthorized with RFC 7807 error.
        """
        # Arrange - Register a user to get a valid user_id
        register_payload = {
            "email": "notoken@example.com",
            "password": "SecurePass123!"
        }
        register_response = await client.post("/api/auth/register", json=register_payload)
        user_id = register_response.json()["user_id"]

        # Act - Try to access tasks without token
        response = await client.get(f"/api/{user_id}/tasks")

        # Assert
        assert response.status_code == 401
        assert response.headers["content-type"] == "application/problem+json"

        error = response.json()
        assert error["type"] == "invalid-authorization-header"
        assert error["title"] == "Invalid Authorization Header"
        assert error["status"] == 401

    @pytest.mark.asyncio
    async def test_access_with_invalid_token_unauthorized(self, client: AsyncClient, db: AsyncSession):
        """
        Test that requests with invalid JWT token are rejected.

        Expected: 401 Unauthorized with RFC 7807 error.
        """
        # Arrange
        register_payload = {
            "email": "invalidtoken@example.com",
            "password": "SecurePass123!"
        }
        register_response = await client.post("/api/auth/register", json=register_payload)
        user_id = register_response.json()["user_id"]

        # Act - Try to access with invalid token
        response = await client.get(
            f"/api/{user_id}/tasks",
            headers={"Authorization": "Bearer invalid.token.here"}
        )

        # Assert
        assert response.status_code == 401
        assert response.headers["content-type"] == "application/problem+json"

        error = response.json()
        assert error["type"] == "invalid-token"
        assert error["status"] == 401

    @pytest.mark.asyncio
    async def test_access_with_expired_token_unauthorized(self, client: AsyncClient, db: AsyncSession):
        """
        Test that requests with expired JWT token are rejected.

        Expected: 401 Unauthorized with RFC 7807 error.
        """
        # Arrange
        from datetime import timedelta
        from uuid import uuid4

        user_id = uuid4()
        # Create expired token
        expired_token = create_access_token(user_id, expires_delta=timedelta(seconds=-1))

        # Act - Try to access with expired token
        response = await client.get(
            f"/api/{user_id}/tasks",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        # Assert
        assert response.status_code == 401
        assert response.headers["content-type"] == "application/problem+json"

        error = response.json()
        assert error["type"] == "invalid-token"
        assert error["status"] == 401

    @pytest.mark.asyncio
    async def test_create_task_requires_authentication(self, client: AsyncClient, db: AsyncSession):
        """
        Test that creating tasks requires authentication.

        Expected: 401 Unauthorized without token.
        """
        # Arrange
        register_payload = {
            "email": "createtask@example.com",
            "password": "SecurePass123!"
        }
        register_response = await client.post("/api/auth/register", json=register_payload)
        user_id = register_response.json()["user_id"]

        task_payload = {
            "title": "New Task",
            "description": "Task description"
        }

        # Act - Try to create task without token
        response = await client.post(
            f"/api/{user_id}/tasks",
            json=task_payload
        )

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_task_requires_authentication(self, client: AsyncClient, db: AsyncSession):
        """
        Test that updating tasks requires authentication.

        Expected: 401 Unauthorized without token.
        """
        # Arrange - Create a user and task
        register_payload = {
            "email": "updatetask@example.com",
            "password": "SecurePass123!"
        }
        register_response = await client.post("/api/auth/register", json=register_payload)
        user_id = register_response.json()["user_id"]

        login_payload = {
            "email": "updatetask@example.com",
            "password": "SecurePass123!"
        }
        login_response = await client.post("/api/auth/login", json=login_payload)
        token = login_response.json()["access_token"]

        # Create a task
        task_payload = {
            "title": "Task to Update",
            "description": "Original description"
        }
        create_response = await client.post(
            f"/api/{user_id}/tasks",
            json=task_payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        task_id = create_response.json()["id"]

        # Act - Try to update task without token
        update_payload = {
            "title": "Updated Task",
            "status": "completed"
        }
        response = await client.put(
            f"/api/{user_id}/tasks/{task_id}",
            json=update_payload
        )

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_task_requires_authentication(self, client: AsyncClient, db: AsyncSession):
        """
        Test that deleting tasks requires authentication.

        Expected: 401 Unauthorized without token.
        """
        # Arrange - Create a user and task
        register_payload = {
            "email": "deletetask@example.com",
            "password": "SecurePass123!"
        }
        register_response = await client.post("/api/auth/register", json=register_payload)
        user_id = register_response.json()["user_id"]

        login_payload = {
            "email": "deletetask@example.com",
            "password": "SecurePass123!"
        }
        login_response = await client.post("/api/auth/login", json=login_payload)
        token = login_response.json()["access_token"]

        # Create a task
        task_payload = {
            "title": "Task to Delete",
            "description": "Will be deleted"
        }
        create_response = await client.post(
            f"/api/{user_id}/tasks",
            json=task_payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        task_id = create_response.json()["id"]

        # Act - Try to delete task without token
        response = await client.delete(f"/api/{user_id}/tasks/{task_id}")

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_user_isolation_on_task_creation(self, client: AsyncClient, db: AsyncSession):
        """
        Test that users cannot create tasks for other users.

        Expected: 403 Forbidden when token user_id doesn't match path user_id.
        """
        # Arrange - Create two users
        user1_register = {
            "email": "creator1@example.com",
            "password": "SecurePass123!"
        }
        user1_response = await client.post("/api/auth/register", json=user1_register)
        user1_id = user1_response.json()["user_id"]

        user1_login = {
            "email": "creator1@example.com",
            "password": "SecurePass123!"
        }
        user1_login_response = await client.post("/api/auth/login", json=user1_login)
        user1_token = user1_login_response.json()["access_token"]

        user2_register = {
            "email": "creator2@example.com",
            "password": "SecurePass123!"
        }
        user2_response = await client.post("/api/auth/register", json=user2_register)
        user2_id = user2_response.json()["user_id"]

        # Act - User 1 tries to create task for User 2
        task_payload = {
            "title": "Unauthorized Task",
            "description": "Should not be created"
        }
        response = await client.post(
            f"/api/{user2_id}/tasks",
            json=task_payload,
            headers={"Authorization": f"Bearer {user1_token}"}
        )

        # Assert
        assert response.status_code == 403
        error = response.json()
        assert error["type"] == "access-denied"
