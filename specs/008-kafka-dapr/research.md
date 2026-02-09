# Research: Kafka + Dapr Event-Driven Architecture

**Feature**: 008-kafka-dapr
**Date**: 2026-02-09
**Status**: Complete

## Overview

This document consolidates research findings for implementing event-driven architecture using Redpanda Cloud and Dapr. All technical decisions have been made and documented in the Decision Table below.

## Research Findings

### 1. Redpanda Cloud Serverless Setup

**Decision**: Use Redpanda Cloud serverless free tier

**Key Findings**:
- Free tier provides sufficient throughput for MVP (up to 10 MB/s ingress, 30 MB/s egress)
- Kafka-compatible API (no code changes needed for Kafka clients)
- Zero infrastructure management (no broker configuration, no storage provisioning)
- SASL/SCRAM authentication with TLS encryption
- Topic creation via Redpanda Console or Kafka Admin API
- Bootstrap servers provided in connection string format

**Connection Configuration**:
```yaml
brokers: "bootstrap.redpanda.cloud:9092"
authType: "password"
saslMechanism: "SCRAM-SHA-256"
saslUsername: "<from Redpanda Console>"
saslPassword: "<from Redpanda Console>"
```

**Topic Configuration**:
- `task-events`: 3 partitions, 7-day retention
- `reminders`: 1 partition, 1-day retention
- `task-updates`: 3 partitions, 1-day retention

**Rationale**: Fastest path to production, zero operational overhead, free tier sufficient for MVP, easy migration to self-hosted if needed.

### 2. Dapr Pub/Sub Best Practices

**Decision**: Use Dapr HTTP API for event publishing, Dapr SDK for subscriptions

**Key Findings**:
- HTTP API simpler for publishing (no SDK dependency in main app)
- SDK provides better subscription management and error handling
- CloudEvents specification compliance built-in
- Consumer groups automatically managed by Dapr
- Retry policies configurable per component
- Dead-letter queue support via component metadata

**Publishing Pattern**:
```python
import httpx

async def publish_event(topic: str, event: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:3500/v1.0/publish/pubsub/{topic}",
            json=event,
            headers={"Content-Type": "application/cloudevents+json"}
        )
        response.raise_for_status()
```

**Subscription Pattern**:
```python
from dapr.ext.fastapi import DaprApp

app = FastAPI()
dapr_app = DaprApp(app)

@dapr_app.subscribe(pubsub="pubsub", topic="task-events")
async def handle_task_event(event: dict):
    # Process event
    pass
```

**Rationale**: HTTP API for publishing keeps main app lightweight, SDK for subscriptions provides robust error handling and retry logic.

### 3. Dapr State Store Patterns

**Decision**: Use PostgreSQL state store for scheduled reminders and consumer offsets

**Key Findings**:
- Reuses existing Neon PostgreSQL database (no new infrastructure)
- Transactional consistency for state operations
- TTL support for automatic cleanup
- Key-value API with JSON value support
- Bulk operations for performance
- State encryption at rest

**State Key Design**:
- `reminder:{task_id}`: Scheduled reminder metadata (TTL: 30 days)
- `consumer_offset:{service}:{topic}`: Event processing offsets (no TTL)
- `sequence:{task_id}`: Event sequence numbers (no TTL)

**State Operations**:
```python
from dapr.clients import DaprClient

async def save_reminder(task_id: str, reminder_data: dict):
    with DaprClient() as client:
        client.save_state(
            store_name="statestore",
            key=f"reminder:{task_id}",
            value=reminder_data,
            state_metadata={"ttlInSeconds": "2592000"}  # 30 days
        )
```

**Rationale**: Leverages existing database, provides transactional consistency, TTL for automatic cleanup.

### 4. Dapr Jobs API

**Decision**: Use Dapr Jobs API for scheduled reminders (not Cron Binding)

**Key Findings**:
- Jobs API supports one-time scheduled jobs (perfect for reminders)
- Cron Binding only supports recurring schedules (not suitable)
- Jobs persist across service restarts
- Jobs can be cancelled programmatically
- Jobs support custom payloads
- Jobs trigger HTTP callbacks at scheduled time

**Job Scheduling Pattern**:
```python
import httpx
from datetime import datetime

async def schedule_reminder(task_id: str, reminder_time: datetime):
    job_data = {
        "schedule": reminder_time.isoformat(),
        "data": {"task_id": task_id},
        "repeats": 0  # One-time job
    }

    async with httpx.AsyncClient() as client:
        await client.post(
            f"http://localhost:3500/v1.0-alpha1/jobs/{task_id}",
            json=job_data
        )
```

**Job Cancellation Pattern**:
```python
async def cancel_reminder(task_id: str):
    async with httpx.AsyncClient() as client:
        await client.delete(
            f"http://localhost:3500/v1.0-alpha1/jobs/{task_id}"
        )
```

**Rationale**: Jobs API designed for one-time scheduled tasks, persists across restarts, supports cancellation.

### 5. Event Schema Design

**Decision**: Use CloudEvents 1.0 specification with custom data payload

**Key Findings**:
- CloudEvents provides standard envelope for event metadata
- Dapr Pub/Sub natively supports CloudEvents
- Idempotency key in event ID field
- Sequence number in custom data field
- Event type follows reverse-DNS naming (com.todo.task.created)
- Timestamp in ISO 8601 format with timezone

**Event Structure**:
```json
{
  "specversion": "1.0",
  "type": "com.todo.task.created",
  "source": "backend-api",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "time": "2026-02-09T10:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "task_id": "uuid",
    "user_id": "uuid",
    "sequence": 123,
    "idempotency_key": "uuid",
    "payload": { /* task-specific data */ }
  }
}
```

**Idempotency Pattern**:
- Event ID serves as idempotency key
- Consumers check if event ID already processed before handling
- Store processed event IDs in Dapr State Store with TTL (7 days)

**Sequence Number Pattern**:
- Monotonically increasing per task
- Stored in Dapr State Store (`sequence:{task_id}`)
- Clients use to detect out-of-order events and gaps

**Rationale**: CloudEvents is industry standard, Dapr native support, clear separation of metadata and payload.

### 6. WebSocket Real-Time Sync

**Decision**: Use FastAPI WebSocket with JWT authentication

**Key Findings**:
- FastAPI has built-in WebSocket support
- JWT token passed in query parameter or header
- Connection manager tracks active connections per user
- Broadcast to all connections for a user on event
- Automatic reconnection with exponential backoff on client
- Heartbeat/ping-pong for connection health

**WebSocket Server Pattern**:
```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)

    async def broadcast(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/tasks")
async def websocket_endpoint(websocket: WebSocket, token: str):
    user_id = verify_jwt(token)
    await manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
```

**Client Reconnection Pattern**:
```typescript
class WebSocketClient {
  private reconnectDelay = 1000;
  private maxReconnectDelay = 30000;

  connect() {
    this.ws = new WebSocket(`ws://localhost:8000/ws/tasks?token=${token}`);

    this.ws.onclose = () => {
      setTimeout(() => {
        this.reconnectDelay = Math.min(
          this.reconnectDelay * 2,
          this.maxReconnectDelay
        );
        this.connect();
      }, this.reconnectDelay);
    };
  }
}
```

**Rationale**: FastAPI native support, JWT authentication reuses existing auth, connection manager enables user-specific broadcasting.

### 7. Email/Push Notification Integration

**Decision**: Use SendGrid for email, Firebase Cloud Messaging for push

**Key Findings**:
- SendGrid free tier: 100 emails/day (sufficient for MVP)
- Firebase Cloud Messaging (FCM) free tier: unlimited messages
- Both have Python SDKs with async support
- Template support for notification content
- Delivery tracking via webhooks
- Retry logic built into SDKs

**Email Notification Pattern**:
```python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

async def send_email_reminder(user_email: str, task_title: str, due_date: str):
    message = Mail(
        from_email='noreply@todo.app',
        to_emails=user_email,
        subject=f'Reminder: {task_title}',
        html_content=f'<p>Your task "{task_title}" is due on {due_date}</p>'
    )

    sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    response = await sg.send(message)
```

**Push Notification Pattern**:
```python
from firebase_admin import messaging

async def send_push_reminder(device_token: str, task_title: str):
    message = messaging.Message(
        notification=messaging.Notification(
            title='Task Reminder',
            body=f'Your task "{task_title}" is due soon'
        ),
        token=device_token
    )

    response = await messaging.send(message)
```

**Rationale**: Free tiers sufficient for MVP, Python SDK support, reliable delivery, easy integration.

### 8. Kubernetes Deployment Patterns

**Decision**: Use Dapr sidecar injection with Helm charts

**Key Findings**:
- Dapr sidecar injected via annotations on Deployment
- Sidecar handles all Dapr API calls (Pub/Sub, State, Jobs)
- ConfigMaps for non-sensitive configuration
- Secrets for credentials (Redpanda, SendGrid, FCM)
- Resource limits prevent resource exhaustion
- Liveness/readiness probes for health checks
- Horizontal Pod Autoscaler (HPA) for scaling

**Dapr Sidecar Injection**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-api
spec:
  template:
    metadata:
      annotations:
        dapr.io/enabled: "true"
        dapr.io/app-id: "backend-api"
        dapr.io/app-port: "8000"
        dapr.io/log-level: "info"
    spec:
      containers:
      - name: backend-api
        image: backend-api:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

**Helm Values Parameterization**:
```yaml
# values.yaml
replicaCount: 2

image:
  repository: backend-api
  tag: latest
  pullPolicy: IfNotPresent

resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
```

**Rationale**: Dapr sidecar pattern standard for Dapr apps, Helm charts enable environment-specific configuration, resource limits prevent noisy neighbor issues.

## Decision Summary

| Decision | Selected Option | Key Benefit |
|----------|----------------|-------------|
| Message Broker | Redpanda Cloud serverless | Zero infrastructure management, free tier |
| Messaging Abstraction | Dapr Pub/Sub | Vendor-neutral, built-in retry/DLQ |
| Event Ordering | Sequence numbers + client-side resolution | Scalable with ordering guarantees |
| Retry Strategy | Exponential backoff (3 retries) + DLQ | Prevents cascading failures |
| Reminder Scheduling | Dapr Jobs API | Exact-time triggers, no polling |
| State Management | PostgreSQL via Dapr State Store | Reuses existing DB, transactional |
| Real-Time Sync | WebSocket | Bidirectional, low latency |
| Notification Channels | Email (SendGrid) + Push (FCM) | Balanced reliability and immediacy |
| Deployment | Dapr sidecar + Helm charts | Standard pattern, environment-agnostic |

## Implementation Readiness

✅ All research complete
✅ All technical decisions made
✅ All patterns documented with code examples
✅ Ready for Phase 1: Design & Contracts

## References

- [Dapr Pub/Sub Documentation](https://docs.dapr.io/developing-applications/building-blocks/pubsub/)
- [Dapr State Management Documentation](https://docs.dapr.io/developing-applications/building-blocks/state-management/)
- [Dapr Jobs API Documentation](https://docs.dapr.io/developing-applications/building-blocks/jobs/)
- [CloudEvents Specification](https://cloudevents.io/)
- [Redpanda Cloud Documentation](https://docs.redpanda.com/current/get-started/cloud/)
- [FastAPI WebSocket Documentation](https://fastapi.tiangolo.com/advanced/websockets/)
- [SendGrid Python SDK](https://github.com/sendgrid/sendgrid-python)
- [Firebase Cloud Messaging](https://firebase.google.com/docs/cloud-messaging)
