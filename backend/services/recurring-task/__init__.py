"""
Recurring Task Service - Standalone FastAPI microservice.

Subscribes to task-events via Dapr Pub/Sub and creates next occurrences
of recurring tasks when they are completed.
"""
