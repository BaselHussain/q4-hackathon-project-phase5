"""
E2E test fixtures for event-driven architecture validation.

These tests require a running Kubernetes cluster with all services deployed.
Set the following environment variables before running:
  - API_BASE_URL: Backend API URL (default: http://localhost:8000)
  - TEST_USER_EMAIL: Test user email
  - TEST_USER_PASSWORD: Test user password
"""
import os
import asyncio
from typing import AsyncGenerator, Dict

import httpx
import pytest
import pytest_asyncio


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "e2etest@example.com")
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "TestPass123!")


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create shared HTTP client for all tests."""
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as client:
        yield client


@pytest_asyncio.fixture(scope="session")
async def auth_headers(http_client: httpx.AsyncClient) -> Dict[str, str]:
    """
    Register and login a test user, return auth headers.

    Attempts login first; if user doesn't exist, registers then logs in.
    """
    # Try login first
    login_resp = await http_client.post("/api/auth/login", json={
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
    })

    if login_resp.status_code != 200:
        # Register user
        register_resp = await http_client.post("/api/auth/register", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
        })
        assert register_resp.status_code in (201, 409), f"Registration failed: {register_resp.text}"

        # Login
        login_resp = await http_client.post("/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
        })

    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    data = login_resp.json()
    return {
        "Authorization": f"Bearer {data['access_token']}",
        "user_id": str(data["user_id"]),
    }


@pytest_asyncio.fixture
async def test_task(http_client: httpx.AsyncClient, auth_headers: Dict[str, str]) -> Dict:
    """Create a test task and return its data. Cleans up after test."""
    user_id = auth_headers["user_id"]
    headers = {"Authorization": auth_headers["Authorization"]}

    resp = await http_client.post(
        f"/api/{user_id}/tasks",
        json={"title": "E2E Test Task", "description": "Created by E2E test"},
        headers=headers,
    )
    assert resp.status_code == 201, f"Task creation failed: {resp.text}"
    task = resp.json()

    yield task

    # Cleanup
    await http_client.delete(f"/api/{user_id}/tasks/{task['id']}", headers=headers)
