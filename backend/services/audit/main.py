"""
Audit Service - Standalone FastAPI microservice for event logging.

This service subscribes to task events via Dapr Pub/Sub and logs them
to the audit_logs table for compliance and debugging.
"""
import logging
from contextlib import asynccontextmanager
from typing import Dict, List

from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel

# Prometheus metrics instrumentation (Spec 9 - T023)
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram

# Structured logging configuration (Spec 9 - T038)
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from utils.structured_logger import get_logger

from .consumer import handle_task_event
from .logger import close_db_connections

logger = get_logger(__name__)


# Pydantic models for request/response validation
class DaprSubscription(BaseModel):
    """Dapr subscription configuration."""
    pubsubname: str
    topic: str
    route: str


class CloudEvent(BaseModel):
    """CloudEvent format for Dapr Pub/Sub."""
    id: str
    source: str
    type: str
    datacontenttype: str = "application/json"
    time: str
    data: Dict


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown tasks.

    Handles:
    - Startup: Log service initialization
    - Shutdown: Close database connections gracefully
    """
    # Startup
    logger.info("Audit Service starting up...")
    yield
    # Shutdown
    logger.info("Audit Service shutting down...")
    await close_db_connections()


# Create FastAPI application
app = FastAPI(
    title="Audit Service",
    description="Event logging and audit trail microservice",
    version="1.0.0",
    lifespan=lifespan
)

# Prometheus metrics instrumentation (Spec 9 - T023)
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics", "/health"],
    env_var_name="ENABLE_METRICS",
)

# Custom metrics for audit log operations
audit_logs_written_total = Counter(
    'audit_logs_written_total',
    'Total number of audit logs written',
    ['event_type']
)

audit_log_write_duration_seconds = Histogram(
    'audit_log_write_duration_seconds',
    'Time to write an audit log entry',
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1]
)

# Instrument the app and expose /metrics endpoint
instrumentator.instrument(app).expose(app, endpoint="/metrics")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for Kubernetes probes.

    Returns:
        Dict: Service status
    """
    return {
        "status": "healthy",
        "service": "audit-service",
        "version": "1.0.0"
    }


@app.get("/dapr/subscribe")
async def subscribe() -> List[DaprSubscription]:
    """
    Dapr subscription endpoint.

    Tells Dapr which topics this service subscribes to and which routes
    to call when events are published.

    Returns:
        List[DaprSubscription]: Subscription configuration
    """
    subscriptions = [
        DaprSubscription(
            pubsubname="pubsub",
            topic="task-events",
            route="/events/task-events"
        )
    ]

    logger.info(
        f"Dapr subscription request: subscribing to {len(subscriptions)} topic(s)"
    )

    return subscriptions


@app.post("/events/task-events", status_code=status.HTTP_200_OK)
async def receive_task_event(event: CloudEvent) -> Response:
    """
    Receive and process task events from Dapr Pub/Sub.

    Handles all task-related events (created, updated, completed, deleted)
    and writes them to the audit log with idempotency.

    Args:
        event: CloudEvent formatted task event

    Returns:
        Response: 200 OK if successfully processed, 500 on error

    Raises:
        HTTPException: 500 if event processing fails
    """
    try:
        logger.info(
            f"Received task event: id={event.id}, type={event.type}, "
            f"source={event.source}"
        )

        # Convert Pydantic model to dict for consumer
        event_dict = event.model_dump()

        # Process event
        success = await handle_task_event(event_dict)

        if success:
            logger.info(f"Successfully processed event {event.id}")
            return Response(status_code=status.HTTP_200_OK)
        else:
            # Log error but return 200 to prevent Dapr from retrying
            # (failed events are already logged and retried internally)
            logger.error(
                f"Failed to process event {event.id}, but returning 200 "
                f"to prevent Dapr retry"
            )
            return Response(status_code=status.HTTP_200_OK)

    except Exception as e:
        logger.error(
            f"Unexpected error processing event {event.id}: {e}",
            exc_info=True
        )
        # Return 200 to prevent Dapr from retrying
        return Response(status_code=status.HTTP_200_OK)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
