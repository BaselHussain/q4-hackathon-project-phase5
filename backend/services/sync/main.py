"""
Real-Time Sync Service - FastAPI WebSocket Server.

This service:
1. Subscribes to task-updates topic via Dapr Pub/Sub
2. Manages WebSocket connections for authenticated users
3. Broadcasts task updates in real-time
"""
import logging
import os
from typing import List, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from consumer import handle_task_update
from websocket import ConnectionManager, verify_ws_token


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Real-Time Sync Service",
    description="WebSocket service for real-time task updates via Dapr Pub/Sub",
    version="1.0.0"
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global connection manager
manager = ConnectionManager()


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    Returns service status and connection metrics.
    """
    return {
        "status": "healthy",
        "service": "sync-service",
        "active_connections": manager.get_connection_count(),
        "active_users": len(manager.active_connections)
    }


@app.get("/dapr/subscribe")
async def subscribe() -> List[Dict[str, str]]:
    """
    Dapr subscription endpoint.

    Tells Dapr to route task-updates topic messages to /events/task-updates.

    Returns:
        List of subscription configurations for Dapr
    """
    logger.info("Dapr subscribe endpoint called")
    return [
        {
            "pubsubname": "pubsub",
            "topic": "task-updates",
            "route": "/events/task-updates"
        }
    ]


@app.post("/events/task-updates")
async def handle_event(event: Dict[str, Any]) -> Dict[str, str]:
    """
    Receive task update events from Dapr Pub/Sub.

    Args:
        event: Task update event from Kafka via Dapr

    Returns:
        Success acknowledgment
    """
    logger.info(f"Received task update event: {event}")

    try:
        # Extract data from Dapr CloudEvent wrapper if present
        data = event.get("data", event)

        await handle_task_update(data, manager)

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error processing event: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/tasks")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token")
) -> None:
    """
    WebSocket endpoint for real-time task updates.

    Requires JWT token in query parameter for authentication.

    Args:
        websocket: WebSocket connection
        token: JWT token from query parameter

    Raises:
        WebSocketDisconnect: When client disconnects
    """
    user_id = None

    try:
        # Verify JWT token and extract user_id
        user_id = verify_ws_token(token)
        logger.info(f"WebSocket connection attempt from user {user_id}")

    except ValueError as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
        return

    # Connect the authenticated user
    await manager.connect(user_id, websocket)

    try:
        # Keep connection alive and handle incoming messages
        while True:
            # Wait for client messages (ping/pong or other control messages)
            data = await websocket.receive_text()
            logger.debug(f"Received message from user {user_id}: {data}")

            # Echo back for ping/pong
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}", exc_info=True)
    finally:
        if user_id:
            manager.disconnect(user_id, websocket)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("SYNC_SERVICE_PORT", "8003"))
    logger.info(f"Starting Real-Time Sync Service on port {port}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
