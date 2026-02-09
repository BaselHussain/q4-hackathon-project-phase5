"""
WebSocket connection manager with JWT authentication.

This module provides WebSocket connection management and JWT token verification
for real-time task updates.
"""
import logging
import os
from typing import Dict, Set

from fastapi import WebSocket, WebSocketDisconnect
from jose import JWTError, jwt


logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections grouped by user_id.

    Handles connection lifecycle and message broadcasting to specific users.
    """

    def __init__(self):
        """Initialize connection manager with empty connection tracking."""
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        logger.info("ConnectionManager initialized")

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        """
        Accept and track a new WebSocket connection.

        Args:
            user_id: The authenticated user's ID
            websocket: The WebSocket connection to track
        """
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)
        logger.info(
            f"User {user_id} connected. Total connections for user: "
            f"{len(self.active_connections[user_id])}"
        )

    def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection from tracking.

        Args:
            user_id: The user's ID
            websocket: The WebSocket connection to remove
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)

            # Clean up empty user connection sets
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

            logger.info(
                f"User {user_id} disconnected. Remaining connections for user: "
                f"{len(self.active_connections.get(user_id, set()))}"
            )

    async def broadcast_to_user(self, user_id: str, message: dict) -> None:
        """
        Send a message to all connections for a specific user.

        Args:
            user_id: The user ID to broadcast to
            message: The message dictionary to send (will be JSON serialized)
        """
        if user_id not in self.active_connections:
            logger.debug(f"No active connections for user {user_id}")
            return

        connections = list(self.active_connections[user_id])
        disconnected = []

        for websocket in connections:
            try:
                await websocket.send_json(message)
            except WebSocketDisconnect:
                logger.warning(f"WebSocket disconnected during broadcast for user {user_id}")
                disconnected.append(websocket)
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {e}")
                disconnected.append(websocket)

        # Clean up disconnected sockets
        for websocket in disconnected:
            self.disconnect(user_id, websocket)

        logger.info(
            f"Broadcasted message to {len(connections) - len(disconnected)} "
            f"connections for user {user_id}"
        )

    def get_connection_count(self) -> int:
        """
        Get the total number of active WebSocket connections.

        Returns:
            Total number of connections across all users
        """
        return sum(len(connections) for connections in self.active_connections.values())


def verify_ws_token(token: str) -> str:
    """
    Verify JWT token and extract user_id.

    Args:
        token: JWT token string

    Returns:
        user_id extracted from token's 'sub' claim

    Raises:
        ValueError: If token is invalid, expired, or missing required claims
    """
    secret_key = os.getenv("BETTER_AUTH_SECRET")
    if not secret_key:
        raise ValueError("BETTER_AUTH_SECRET environment variable not set")

    algorithm = "HS256"

    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        user_id = payload.get("sub")

        if not user_id:
            raise ValueError("Token missing 'sub' claim")

        logger.debug(f"Token verified successfully for user {user_id}")
        return user_id

    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise ValueError(f"Invalid token: {e}")
