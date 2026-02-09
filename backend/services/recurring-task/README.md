# Recurring Task Service

Standalone FastAPI microservice that subscribes to Kafka task events via Dapr Pub/Sub and automatically creates next occurrences of recurring tasks when they are completed.

## Architecture

- **Runtime**: Python 3.11+ with FastAPI
- **Message Broker**: Kafka/Redpanda via Dapr Pub/Sub
- **Communication**: Dapr HTTP API for subscriptions, httpx for backend API calls
- **Deployment**: Standalone service with Dapr sidecar injection

## Service Flow

1. Service exposes `/dapr/subscribe` endpoint with subscription configuration
2. Dapr sidecar reads subscription config on startup
3. When a `task.completed` event is published to `task-events` topic:
   - Dapr routes the CloudEvent to `/events/task-events`
   - Service checks if task has `recurring_pattern != "none"`
   - If recurring, calculates next due date based on pattern
   - Creates new task via backend API with exponential backoff retry
4. Idempotency is guaranteed by tracking processed event IDs

## Recurrence Patterns

| Pattern | Increment |
|---------|-----------|
| `daily` | +1 day |
| `weekly` | +7 days |
| `monthly` | +1 month (handles end-of-month) |
| `yearly` | +1 year (handles leap years) |
| `none` | No recurrence |

## Endpoints

### Health Check
```
GET /health
```
Returns service health status for Kubernetes probes.

### Dapr Subscription
```
GET /dapr/subscribe
```
Returns subscription configuration for Dapr:
```json
[
  {
    "pubsubname": "pubsub",
    "topic": "task-events",
    "route": "/events/task-events"
  }
]
```

### Event Receiver
```
POST /events/task-events
```
Receives CloudEvents from Dapr when task events are published.

## Configuration

Environment variables:

- `DAPR_HTTP_PORT`: Port where Dapr sidecar is running (default: `3502`)
- `BACKEND_API_URL`: URL of main backend API (default: `http://localhost:8000`)
- `PORT`: Service listening port (default: `8001`)

## Development

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Service
```bash
# Without Dapr (events will be logged but not processed)
python main.py

# With Dapr sidecar
dapr run --app-id recurring-task-service \
         --app-port 8001 \
         --dapr-http-port 3502 \
         --resources-path ./dapr/components \
         -- python main.py
```

### Run Tests
```bash
pytest tests/ -v
```

## Production Deployment

### Kubernetes with Dapr

The service should be deployed with Dapr sidecar injection:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: recurring-task-service
spec:
  template:
    metadata:
      annotations:
        dapr.io/enabled: "true"
        dapr.io/app-id: "recurring-task-service"
        dapr.io/app-port: "8001"
        dapr.io/app-protocol: "http"
    spec:
      containers:
      - name: service
        image: recurring-task-service:latest
        ports:
        - containerPort: 8001
        env:
        - name: BACKEND_API_URL
          value: "http://backend-api:8000"
        - name: DAPR_HTTP_PORT
          value: "3500"
```

### Retry and Error Handling

- **Idempotency**: Processed event IDs are tracked in-memory (use Dapr State Store in production)
- **Retry Strategy**: 3 attempts with exponential backoff (1s, 5s, 25s)
- **Client Errors (4xx)**: Not retried (malformed requests)
- **Server Errors (5xx)**: Retried with backoff
- **Connection Errors**: Retried with backoff

### Observability

- **Logging**: Structured logs with correlation IDs
- **Health Checks**: `/health` endpoint for liveness/readiness probes
- **Metrics**: Expose Prometheus metrics via Dapr (future enhancement)

## Event Format

### Input (CloudEvent from task-events topic)

```json
{
  "specversion": "1.0",
  "type": "com.todo.task.completed",
  "source": "backend-api",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "time": "2024-01-15T10:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "task_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "user-456",
    "sequence": 5,
    "idempotency_key": "550e8400-e29b-41d4-a716-446655440000",
    "payload": {
      "title": "Daily standup",
      "description": "Team sync meeting",
      "priority": "high",
      "tags": ["work", "meeting"],
      "recurring_pattern": "daily",
      "due_date": "2024-01-15T10:00:00+00:00"
    }
  }
}
```

### Output (Task creation request to backend API)

```json
{
  "title": "Daily standup",
  "description": "Team sync meeting",
  "priority": "high",
  "tags": ["work", "meeting"],
  "recurrence": "daily",
  "due_date": "2024-01-16T10:00:00+00:00"
}
```

## Testing

### Unit Tests

- `test_daily_recurrence`: Validates +1 day calculation
- `test_weekly_recurrence`: Validates +7 days calculation
- `test_monthly_recurrence`: Validates month increment with edge cases
- `test_yearly_recurrence`: Validates year increment with leap years
- `test_no_recurrence_returns_none`: Validates "none" pattern handling
- `test_idempotency_prevents_duplicates`: Validates duplicate prevention

### Integration Testing

1. Start Kafka/Redpanda cluster
2. Deploy Dapr with Kafka Pub/Sub component
3. Start backend API service
4. Start recurring task service with Dapr sidecar
5. Publish test events to `task-events` topic
6. Verify new tasks are created with correct due dates

## Limitations (MVP)

- In-memory idempotency tracking (use Dapr State Store for production)
- Simplified authentication (X-User-ID header, replace with JWT)
- No metrics/tracing (add OpenTelemetry for production)
- Basic error handling (add circuit breaker for production)

## Future Enhancements

1. **Persistent Idempotency**: Use Dapr State Store or Redis
2. **Service Authentication**: Use service account JWT tokens
3. **Circuit Breaker**: Add resilience patterns with Dapr Resiliency
4. **Metrics**: Expose Prometheus metrics via Dapr
5. **Dead Letter Queue**: Route failed events to DLQ for manual review
6. **Custom Intervals**: Support "every 2 weeks", "every 3 months", etc.
7. **Time Zone Support**: Calculate next due dates in user's timezone
