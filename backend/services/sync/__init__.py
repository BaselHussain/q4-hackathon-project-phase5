"""
Real-Time Sync Service for Task Updates.

This package implements a standalone FastAPI microservice that:
- Subscribes to Kafka task-updates topic via Dapr Pub/Sub
- Manages WebSocket connections for real-time task synchronization
- Broadcasts task updates to authenticated users
"""
