"""
Notification Service - FastAPI microservice for task reminders.

Subscribes to reminders topic via Dapr Pub/Sub.
Schedules reminders using Dapr Jobs API.
Sends notifications via email and push notifications.
"""
import logging
import os
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from consumer import handle_reminder_event
from scheduler import send_reminder_notification

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Environment configuration
DAPR_HTTP_PORT = os.getenv("DAPR_HTTP_PORT", "3500")
APP_PORT = os.getenv("APP_PORT", "8002")

# FastAPI app initialization
app = FastAPI(
    title="Notification Service",
    description="Schedules and sends task reminder notifications",
    version="1.0.0"
)


@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes liveness/readiness probes."""
    return {
        "status": "healthy",
        "service": "notification-service",
        "dapr_http_port": DAPR_HTTP_PORT
    }


@app.get("/dapr/subscribe")
async def dapr_subscribe():
    """
    Dapr Pub/Sub subscription endpoint.

    Returns subscription configuration for the reminders topic.
    Routes events to /events/reminders POST endpoint.
    """
    subscriptions = [
        {
            "pubsubname": "pubsub",
            "topic": "reminders",
            "route": "/events/reminders"
        }
    ]
    logger.info(f"Dapr subscriptions configured: {subscriptions}")
    return subscriptions


@app.post("/events/reminders")
async def handle_reminders_event(request: Request):
    """
    Receive reminder events from Dapr Pub/Sub.

    Event types:
    - com.todo.reminder.schedule: Schedule a new reminder
    - com.todo.reminder.cancel: Cancel an existing reminder
    """
    try:
        body = await request.json()
        logger.info(f"Received reminder event: {body.get('type', 'unknown')}")

        # Extract CloudEvent data
        event_type = body.get("type")
        event_data = body.get("data", {})

        if not event_type:
            logger.error("Event missing 'type' field")
            return JSONResponse(
                status_code=400,
                content={"error": "Event missing 'type' field"}
            )

        # Process event
        await handle_reminder_event(body)

        return JSONResponse(
            status_code=200,
            content={"status": "success"}
        )

    except Exception as e:
        logger.error(f"Error processing reminder event: {str(e)}", exc_info=True)
        # Return 200 to avoid Dapr retries for application logic errors
        return JSONResponse(
            status_code=200,
            content={"status": "error", "message": str(e)}
        )


@app.post("/jobs/reminder-{task_id}")
async def handle_reminder_job(task_id: str, request: Request):
    """
    Receive Dapr Jobs API callback when a scheduled reminder is due.

    Dapr sends POST request to this endpoint when job triggers.
    Extracts task data from job payload and sends notifications.

    Args:
        task_id: Task ID from URL path parameter
        request: FastAPI request containing job data payload
    """
    try:
        body = await request.json()
        logger.info(f"Reminder job triggered for task_id={task_id}")

        # Extract job data payload
        job_data = body.get("data", {})

        if not job_data:
            logger.warning(f"Job callback missing data payload for task_id={task_id}")
            return JSONResponse(
                status_code=200,
                content={"status": "no_data"}
            )

        # Send notifications
        await send_reminder_notification(task_id, job_data)

        return JSONResponse(
            status_code=200,
            content={"status": "success"}
        )

    except Exception as e:
        logger.error(f"Error handling reminder job for task_id={task_id}: {str(e)}", exc_info=True)
        # Return 200 to avoid Dapr retries
        return JSONResponse(
            status_code=200,
            content={"status": "error", "message": str(e)}
        )


if __name__ == "__main__":
    import uvicorn

    port = int(APP_PORT)
    logger.info(f"Starting Notification Service on port {port}")
    logger.info(f"Dapr HTTP port: {DAPR_HTTP_PORT}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
