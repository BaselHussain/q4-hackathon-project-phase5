"""
Unit tests for WebSocket connection manager.

Tests connection management, broadcasting, and connection counting.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from websocket import ConnectionManager


@pytest.fixture
def manager():
    """Create a fresh ConnectionManager instance for each test."""
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket instance."""
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


@pytest.mark.asyncio
async def test_connection_manager_connect(manager, mock_websocket):
    """
    Test that ConnectionManager correctly accepts and tracks connections.

    Given: A ConnectionManager and a mock WebSocket
    When: connect() is called with a user_id and websocket
    Then: The websocket should be accepted and added to active_connections
    """
    user_id = "test-user-123"

    # Connect the websocket
    await manager.connect(user_id, mock_websocket)

    # Verify websocket.accept() was called
    mock_websocket.accept.assert_called_once()

    # Verify user_id is in active_connections
    assert user_id in manager.active_connections

    # Verify websocket is tracked for this user
    assert mock_websocket in manager.active_connections[user_id]

    # Verify connection count
    assert manager.get_connection_count() == 1


@pytest.mark.asyncio
async def test_connection_manager_connect_multiple_users(manager):
    """
    Test that ConnectionManager handles multiple users correctly.

    Given: A ConnectionManager
    When: Multiple users connect with their websockets
    Then: All users should be tracked separately
    """
    ws1 = MagicMock()
    ws1.accept = AsyncMock()
    ws2 = MagicMock()
    ws2.accept = AsyncMock()

    await manager.connect("user-1", ws1)
    await manager.connect("user-2", ws2)

    assert "user-1" in manager.active_connections
    assert "user-2" in manager.active_connections
    assert ws1 in manager.active_connections["user-1"]
    assert ws2 in manager.active_connections["user-2"]
    assert manager.get_connection_count() == 2


@pytest.mark.asyncio
async def test_connection_manager_connect_same_user_multiple_sockets(manager):
    """
    Test that ConnectionManager handles multiple connections from the same user.

    Given: A ConnectionManager
    When: The same user connects with multiple websockets
    Then: All websockets should be tracked for that user
    """
    user_id = "user-multi"
    ws1 = MagicMock()
    ws1.accept = AsyncMock()
    ws2 = MagicMock()
    ws2.accept = AsyncMock()

    await manager.connect(user_id, ws1)
    await manager.connect(user_id, ws2)

    assert user_id in manager.active_connections
    assert ws1 in manager.active_connections[user_id]
    assert ws2 in manager.active_connections[user_id]
    assert len(manager.active_connections[user_id]) == 2
    assert manager.get_connection_count() == 2


def test_connection_manager_disconnect(manager, mock_websocket):
    """
    Test that ConnectionManager correctly removes disconnected websockets.

    Given: A connected websocket
    When: disconnect() is called
    Then: The websocket should be removed from active_connections
    """
    user_id = "test-user-456"

    # Manually add connection (bypassing async accept)
    manager.active_connections[user_id] = {mock_websocket}

    # Disconnect
    manager.disconnect(user_id, mock_websocket)

    # Verify user_id is removed (empty set cleaned up)
    assert user_id not in manager.active_connections

    # Verify connection count is zero
    assert manager.get_connection_count() == 0


def test_connection_manager_disconnect_one_of_multiple(manager):
    """
    Test disconnecting one websocket when user has multiple connections.

    Given: A user with multiple websocket connections
    When: One connection is disconnected
    Then: Only that connection should be removed, others remain
    """
    user_id = "user-multi-disconnect"
    ws1 = MagicMock()
    ws2 = MagicMock()

    # Manually add connections
    manager.active_connections[user_id] = {ws1, ws2}

    # Disconnect one websocket
    manager.disconnect(user_id, ws1)

    # Verify ws1 is removed but ws2 remains
    assert user_id in manager.active_connections
    assert ws1 not in manager.active_connections[user_id]
    assert ws2 in manager.active_connections[user_id]
    assert manager.get_connection_count() == 1


@pytest.mark.asyncio
async def test_broadcast_to_user(manager, mock_websocket):
    """
    Test that ConnectionManager broadcasts messages to all user connections.

    Given: A user with connected websocket(s)
    When: broadcast_to_user() is called with a message
    Then: The message should be sent to all user's connections
    """
    user_id = "broadcast-user"
    message = {"type": "task_updated", "task_id": "123"}

    # Manually add connection
    manager.active_connections[user_id] = {mock_websocket}

    # Broadcast message
    await manager.broadcast_to_user(user_id, message)

    # Verify send_json was called with the message
    mock_websocket.send_json.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_broadcast_to_user_multiple_connections(manager):
    """
    Test broadcasting to a user with multiple WebSocket connections.

    Given: A user with multiple websocket connections
    When: broadcast_to_user() is called
    Then: The message should be sent to all connections
    """
    user_id = "multi-broadcast-user"
    message = {"type": "task_created", "task_id": "456"}

    ws1 = MagicMock()
    ws1.send_json = AsyncMock()
    ws2 = MagicMock()
    ws2.send_json = AsyncMock()

    manager.active_connections[user_id] = {ws1, ws2}

    await manager.broadcast_to_user(user_id, message)

    # Verify both websockets received the message
    ws1.send_json.assert_called_once_with(message)
    ws2.send_json.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_broadcast_to_user_no_connections(manager):
    """
    Test broadcasting to a user with no active connections.

    Given: A user with no active connections
    When: broadcast_to_user() is called
    Then: No error should occur (graceful handling)
    """
    user_id = "no-connections-user"
    message = {"type": "task_deleted", "task_id": "789"}

    # Should not raise exception
    await manager.broadcast_to_user(user_id, message)

    # Verify user_id is not in active_connections
    assert user_id not in manager.active_connections


def test_get_connection_count_empty(manager):
    """
    Test connection count for an empty ConnectionManager.

    Given: A ConnectionManager with no connections
    When: get_connection_count() is called
    Then: It should return 0
    """
    assert manager.get_connection_count() == 0


def test_get_connection_count_multiple_users(manager):
    """
    Test connection count with multiple users and connections.

    Given: Multiple users with varying numbers of connections
    When: get_connection_count() is called
    Then: It should return the total count of all connections
    """
    ws1 = MagicMock()
    ws2 = MagicMock()
    ws3 = MagicMock()

    manager.active_connections["user-1"] = {ws1, ws2}
    manager.active_connections["user-2"] = {ws3}

    assert manager.get_connection_count() == 3
