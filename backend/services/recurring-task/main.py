"""
Recurring Task Service - FastAPI application.

Provides Dapr Pub/Sub subscription endpoints and health check.
Delegates event processing to consumer module.
"""
import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from consumer import handle_task_event

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Environment configuration
SERVICE_NAME = "recurring-task-service"
DAPR_HTTP_PORT = os.getenv("DAPR_HTTP_PORT", "3502")
PUBSUB_NAME = "pubsub"
TOPIC_TASK_EVENTS = "task-events"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    logger.info(f"Starting {SERVICE_NAME}")
    logger.info(f"Dapr sidecar expected on port {DAPR_HTTP_PORT}")
    logger.info(f"Subscribing to topic: {TOPIC_TASK_EVENTS}")
    yield
    logger.info(f"Shutting down {SERVICE_NAME}")


app = FastAPI(
    title="Recurring Task Service",
    description="Microservice that creates next occurrences of recurring tasks",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint for Kubernetes liveness/readiness probes.

    Returns:
        Status indicating service health
    """
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
    }


@app.get("/dapr/subscribe")
async def dapr_subscribe() -> list[dict[str, Any]]:
    """
    Dapr Pub/Sub subscription endpoint.

    Returns subscription configuration that tells Dapr which topics
    this service wants to subscribe to and which endpoint to route
    events to.

    Returns:
        List of subscription configurations
    """
    subscriptions = [
        {
            "pubsubname": PUBSUB_NAME,
            "topic": TOPIC_TASK_EVENTS,
            "route": "/events/task-events",
        }
    ]
    logger.info(f"Dapr subscription configuration: {subscriptions}")
    return subscriptions


@app.post("/events/task-events")
async def receive_task_event(request: Request) -> JSONResponse:
    """
    Receive task lifecycle events from Dapr Pub/Sub.

    This endpoint is called by Dapr when a new event is published
    to the task-events topic. Events follow CloudEvents 1.0 format.

    Args:
        request: The incoming HTTP request containing the CloudEvent

    Returns:
        JSONResponse with processing status

    Raises:
        HTTPException: If event processing fails
    """
    try:
        # Parse CloudEvent from request body
        event = await request.json()
        logger.info(
            f"Received event: type={event.get('type')}, "
            f"id={event.get('id')}"
        )

        # Delegate to consumer for processing
        success = await handle_task_event(event)

        if success:
            return JSONResponse(
                status_code=200,
                content={"status": "processed"},
            )
        else:
            # Return 200 to acknowledge receipt even if processing failed
            # to prevent Dapr from retrying indefinitely
            logger.warning(
                f"Event {event.get('id')} processing failed but "
                "returning 200 to prevent retry"
            )
            return JSONResponse(
                status_code=200,
                content={"status": "failed"},
            )

    except Exception as e:
        logger.error(f"Error receiving event: {e}", exc_info=True)
        # Return 500 to trigger Dapr retry with exponential backoff
        raise HTTPException(
            status_code=500,
            detail=f"Event processing error: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False,
    )
