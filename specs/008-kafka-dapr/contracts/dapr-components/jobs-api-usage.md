# Dapr Jobs API Configuration
#
# Note: Dapr Jobs API is a built-in feature and does not require a separate component.
# This file documents the Jobs API usage patterns for reference.
#
# Jobs API is accessed via HTTP endpoints:
# - POST   /v1.0-alpha1/jobs/{jobName}        - Schedule a job
# - GET    /v1.0-alpha1/jobs/{jobName}        - Get job details
# - DELETE /v1.0-alpha1/jobs/{jobName}        - Cancel a job
#
# Job Payload Structure:
# {
#   "schedule": "2026-02-10T09:45:00Z",  # ISO 8601 timestamp for one-time job
#   "data": {                             # Custom payload passed to callback
#     "task_id": "uuid",
#     "user_id": "uuid"
#   },
#   "repeats": 0,                         # 0 for one-time job, N for N repeats
#   "dueTime": "15m"                      # Alternative: relative time (e.g., "15m", "1h")
# }
#
# Job Callback:
# When job triggers, Dapr sends POST request to:
# http://localhost:{APP_PORT}/jobs/{jobName}
#
# Example Usage (Notification Service):
#
# Schedule reminder:
# POST http://localhost:3500/v1.0-alpha1/jobs/reminder-{task_id}
# {
#   "schedule": "2026-02-10T09:45:00Z",
#   "data": {"task_id": "uuid", "user_id": "uuid"},
#   "repeats": 0
# }
#
# Cancel reminder:
# DELETE http://localhost:3500/v1.0-alpha1/jobs/reminder-{task_id}
#
# Receive callback in Notification Service:
# @app.post("/jobs/reminder-{task_id}")
# async def handle_reminder_job(job_data: dict):
#     task_id = job_data["data"]["task_id"]
#     # Send notification
#
# Jobs API Features:
# - Persists jobs across service restarts
# - Supports one-time and recurring schedules
# - Supports cancellation
# - Supports custom payloads
# - Automatic retry on callback failure
#
# Jobs API is enabled by default in Dapr runtime (no component needed)
