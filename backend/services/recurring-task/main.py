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

# Prometheus metrics instrumentation (Spec 9 - T020)
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram

# Structured logging configuration (Spec 9 - T035)
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from utils.structured_logger import get_logger

from consumer import handle_task_event

logger = get_logger(__name__)

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

# Prometheus metrics instrumentation (Spec 9 - T020)
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics", "/health"],
    env_var_name="ENABLE_METRICS",
)

# Custom metrics for recurring task processing
recurring_tasks_processed_total = Counter(
    'recurring_tasks_processed_total',
    'Total number of recurring tasks processed',
    ['status']
)

recurring_tasks_created_total = Counter(
    'recurring_tasks_created_total',
    'Total number of new task instances created from recurring tasks'
)

recurring_task_processing_duration_seconds = Histogram(
    'recurring_task_processing_duration_seconds',
    'Time to process all recurring tasks in one cycle',
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
)

# Instrument the app and expose /metrics endpoint
instrumentator.instrument(app).expose(app, endpoint="/metrics")


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
