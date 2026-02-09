# Implementation Plan: Kafka + Dapr Event-Driven Architecture

**Branch**: `008-kafka-dapr` | **Date**: 2026-02-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-kafka-dapr/spec.md`

## Summary

Add event-driven architecture using Redpanda Cloud serverless and Dapr integration to enable decoupled, scalable todo features. Core capabilities include automatic recurring task creation, timely reminders via email/push notifications, real-time task synchronization across clients, and comprehensive audit logging. All services communicate via Dapr Pub/Sub (no direct Kafka clients), use Dapr State Store for persistence, and leverage Dapr Jobs API for scheduled reminders.

**Technical Approach**: Extend existing FastAPI backend to publish task events (created, updated, completed, deleted) to Redpanda topics via Dapr HTTP API. Build four new microservices as event consumers: (1) Recurring Task Service creates next task occurrence on completion, (2) Notification Service schedules and sends reminders, (3) Audit Service logs all operations, (4) Real-Time Sync Service broadcasts updates to WebSocket clients. Use event sequence numbers for ordering, exponential backoff retry (3 attempts), and idempotency keys to prevent duplicates.

## Technical Context

**Language/Version**: Python 3.11+ (backend services), TypeScript/Next.js 16+ (frontend)
**Primary Dependencies**:
- Backend: FastAPI 0.109+, Dapr SDK 1.12+, SQLModel 0.0.14+, asyncpg 0.29+, websockets, croniter
- Frontend: Next.js 16+, React 19, WebSocket client
- Infrastructure: Dapr 1.12+, Redpanda Cloud (Kafka-compatible), Helm 3.x, kubectl 1.28+

**Storage**:
- Primary: Neon Serverless PostgreSQL (existing, extended with audit_logs table)
- State: Dapr State Store backed by PostgreSQL (scheduled reminders, consumer offsets)
- Events: Redpanda Cloud serverless (task-events, reminders, task-updates topics)

**Testing**:
- Backend: pytest for unit tests, integration tests for event flows
- E2E: Minikube deployment tests in CI pipeline
- Contract: Event schema validation tests

**Target Platform**:
- Local: Minikube 1.32+ with Dapr runtime
- Cloud: Azure AKS, Google GKE, or Oracle OKE (Kubernetes 1.28+)

**Project Type**: Web application with event-driven microservices architecture

**Performance Goals**:
- Recurring task creation: <5 seconds after completion event
- Reminder delivery: <30 seconds of scheduled time
- Real-time sync: <2 seconds to all connected clients
- Event processing: 1000 concurrent operations without loss
- Retry success rate: 99.9% eventual success

**Constraints**:
- No direct Kafka client libraries - all messaging via Dapr Pub/Sub HTTP API
- No polling - use Dapr Jobs API for scheduled reminders
- Stateless services - all state in Dapr State Store or database
- Event-driven only - no direct service-to-service API calls
- Idempotency required - use event IDs to prevent duplicate processing

**Scale/Scope**:
- 4 new microservices (recurring, notification, audit, sync)
- 3 Redpanda topics (task-events, reminders, task-updates)
- 5 Dapr components (pubsub, statestore, scheduler, secrets, service invocation)
- 1000 concurrent task operations target
- 90-day audit log retention

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Educational Clarity ✅ PASS
- README.md will contain Minikube setup script with exact commands
- Dapr component YAML files will be documented with inline comments
- Event schemas will be documented in contracts/
- Architecture diagram will show event flow between services
- All environment variables documented in .env.example

### II. Engineering Accuracy ✅ PASS
- Redpanda Cloud serverless selected (Kafka-compatible, free tier)
- Dapr Pub/Sub for all messaging (no direct Kafka clients)
- Dapr State Store for PostgreSQL state management
- Dapr Jobs API for scheduled reminders (no polling)
- Event sequence numbers for ordering
- Exponential backoff retry (1s, 5s, 25s) with dead-letter queue
- Idempotency keys in all events

### III. Practical Applicability ✅ PASS
- Runnable on Minikube with setup script
- Deployable to Azure AKS, Google GKE, Oracle OKE
- Helm charts parameterized for different environments
- .env.example files for all services
- Single command to start entire stack locally

### IV. Spec-Driven Development ✅ PASS
- This is Spec 8 (Kafka + Dapr Event-Driven Architecture)
- Follows approved spec in specs/008-kafka-dapr/spec.md
- All clarifications resolved (notification channels, broker selection, ordering, retry, audit access)
- Plan.md (this file) documents technical approach
- Tasks.md will break down into testable implementation steps

### V. Ethical Responsibility ✅ PASS
- Existing Better Auth + JWT preserved from Phase 2
- User isolation enforced - events include user_id
- Dapr Secrets component for credentials (Redpanda, email/push services)
- Kubernetes Secrets for sensitive configuration
- Audit logs respect user privacy (users see only own history)
- No credentials in code or logs

### VI. Reproducibility & Open Knowledge ✅ PASS
- Public GitHub repository
- .env.example files for all services
- Exact tool versions documented (Python 3.11+, Node.js 20+, Helm 3.x, Dapr 1.12+)
- Dependency lock files (requirements.txt, package-lock.json)
- Minikube setup script works on fresh installation
- Architecture documentation with diagrams

### VII. Zero Broken State ✅ PASS
- Feature branch (008-kafka-dapr) for all work
- PR required before merge to main
- CI/CD pipeline tests on Minikube before merge
- Health check endpoints for all services
- Graceful error handling with exponential backoff retry
- State preserved across restarts (Dapr State Store)

**Gate Result**: ✅ ALL GATES PASS - Proceed to Phase 0 research

## Project Structure

### Documentation (this feature)

```text
specs/008-kafka-dapr/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (in progress)
├── research.md          # Phase 0 output (to be generated)
├── data-model.md        # Phase 1 output (to be generated)
├── quickstart.md        # Phase 1 output (to be generated)
├── contracts/           # Phase 1 output (to be generated)
│   ├── events/
│   │   ├── task-event.schema.json
│   │   ├── reminder-event.schema.json
│   │   └── task-update-event.schema.json
│   └── dapr-components/
│       ├── pubsub.kafka.yaml
│       ├── statestore.postgresql.yaml
│       ├── scheduler.yaml
│       └── secretstores.kubernetes.yaml
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
# Web application structure (existing + new services)

backend/
├── app/
│   ├── main.py                    # Existing FastAPI app
│   ├── routers/
│   │   └── tasks.py               # Extended with event publishing
│   └── middleware/
│       └── auth.py                # Existing JWT middleware
├── models/
│   ├── task.py                    # Extended with recurring, priority, tags
│   └── audit_log.py               # NEW: Audit log model
├── schemas/
│   ├── task.py                    # Extended schemas
│   └── events.py                  # NEW: Event schemas
├── events/
│   ├── publisher.py               # NEW: Dapr Pub/Sub helper
│   └── schemas.py                 # NEW: Event payload definitions
├── services/
│   ├── recurring-task/            # NEW: Recurring Task Service
│   │   ├── main.py
│   │   ├── consumer.py
│   │   └── task_creator.py
│   ├── notification/              # NEW: Notification Service
│   │   ├── main.py
│   │   ├── consumer.py
│   │   ├── scheduler.py
│   │   └── notifiers/
│   │       ├── email.py
│   │       └── push.py
│   ├── audit/                     # NEW: Audit Service
│   │   ├── main.py
│   │   ├── consumer.py
│   │   └── logger.py
│   └── sync/                      # NEW: Real-Time Sync Service
│       ├── main.py
│       ├── consumer.py
│       └── websocket.py
├── requirements.txt               # Extended with dapr, websockets, croniter
└── tests/
    ├── unit/
    ├── integration/
    │   └── test_event_flows.py    # NEW: Event flow tests
    └── contract/
        └── test_event_schemas.py  # NEW: Event schema tests

frontend/
├── src/
│   ├── components/
│   │   └── TaskList.tsx           # Extended with real-time updates
│   ├── hooks/
│   │   └── useWebSocket.ts        # NEW: WebSocket hook
│   └── services/
│       └── websocket.ts           # NEW: WebSocket client
└── package.json                   # Extended with WebSocket dependencies

dapr-components/                   # NEW: Dapr component configurations
├── pubsub.kafka.yaml              # Redpanda Pub/Sub component
├── statestore.postgresql.yaml     # PostgreSQL State Store component
├── scheduler.yaml                 # Jobs API component
└── secretstores.kubernetes.yaml   # Kubernetes Secrets component

helm/                              # NEW: Helm charts for deployment
├── backend/
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       ├── deployment.yaml
│       ├── service.yaml
│       └── dapr-annotations.yaml
├── recurring-task/
│   └── [similar structure]
├── notification/
│   └── [similar structure]
├── audit/
│   └── [similar structure]
└── sync/
    └── [similar structure]

.github/
└── workflows/
    ├── build-test.yml             # NEW: Build and test workflow
    ├── deploy-staging.yml         # NEW: Deploy to staging
    └── deploy-production.yml      # NEW: Deploy to production

scripts/
├── setup-minikube.sh              # NEW: Minikube + Dapr + Kafka setup
└── deploy-local.sh                # NEW: Local deployment script
```

**Structure Decision**: Web application with event-driven microservices. Existing backend/ and frontend/ directories extended with new event publishing and WebSocket capabilities. Four new microservices in backend/services/ for event consumption. Dapr components in dapr-components/ for Pub/Sub, State Store, Jobs API, and Secrets. Helm charts in helm/ for Kubernetes deployment.

## Complexity Tracking

> **No violations - all Constitution Check gates passed**

This feature adds architectural complexity (event-driven microservices) but is justified by:
- **Scalability**: Event-driven architecture allows independent scaling of services
- **Decoupling**: Services communicate via events, not direct API calls
- **Reliability**: Dapr provides built-in retry, state management, and observability
- **Maintainability**: Each service has single responsibility (recurring, notification, audit, sync)

The complexity is managed through:
- Dapr abstraction layer (no direct Kafka client code)
- Clear event schemas and contracts
- Comprehensive documentation and setup scripts
- Helm charts for consistent deployment

## Phase 0: Research & Decision Making

### Research Topics

1. **Redpanda Cloud Setup**
   - Serverless free tier provisioning process
   - Connection configuration (bootstrap servers, SASL/SSL)
   - Topic creation and management
   - Kafka compatibility verification

2. **Dapr Pub/Sub Best Practices**
   - HTTP API vs SDK for event publishing
   - Subscription configuration (routes, metadata)
   - Consumer group management
   - Error handling and retry policies

3. **Dapr State Store Patterns**
   - PostgreSQL state store configuration
   - State key design for scheduled reminders
   - Transaction support and consistency
   - State TTL for cleanup

4. **Dapr Jobs API**
   - Job scheduling patterns for reminders
   - Job persistence and recovery
   - Job cancellation on task completion
   - Cron expression vs one-time jobs

5. **Event Schema Design**
   - CloudEvents specification compliance
   - Event versioning strategy
   - Idempotency key patterns
   - Sequence number implementation

6. **WebSocket Real-Time Sync**
   - FastAPI WebSocket support
   - Connection management and reconnection
   - Message broadcasting patterns
   - Client-side event ordering

7. **Email/Push Notification Integration**
   - Email service options (SendGrid, AWS SES, SMTP)
   - Push notification services (Firebase Cloud Messaging, OneSignal)
   - Notification template management
   - Delivery tracking and retry

8. **Kubernetes Deployment Patterns**
   - Dapr sidecar injection annotations
   - Service-to-service communication
   - ConfigMap and Secret management
   - Resource limits and autoscaling

### Decision Table

| Decision | Options Considered | Selected | Rationale |
|----------|-------------------|----------|-----------|
| Message Broker | Kafka (Strimzi), Redpanda Cloud, Confluent Cloud | **Redpanda Cloud serverless** | Free tier, Kafka-compatible, zero infrastructure management, fastest setup for MVP |
| Messaging Abstraction | Direct Kafka client, Dapr Pub/Sub | **Dapr Pub/Sub** | Vendor-neutral, built-in retry/DLQ, easier testing, aligns with constitution requirement |
| Event Ordering | Single partition per task, Sequence numbers, Vector clocks | **Sequence numbers + client-side resolution** | Balances scalability with ordering guarantees, industry standard for real-time collaboration |
| Retry Strategy | Immediate retry, Exponential backoff, Unlimited retry | **Exponential backoff (3 retries) + DLQ** | Prevents cascading failures, ensures eventual processing, aligns with 99.9% success target |
| Reminder Scheduling | Polling, Dapr Cron Binding, Dapr Jobs API | **Dapr Jobs API** | Exact-time triggers, no polling overhead, built-in persistence and recovery |
| State Management | In-memory, Redis, PostgreSQL via Dapr | **PostgreSQL via Dapr State Store** | Reuses existing Neon DB, transactional consistency, no new infrastructure |
| Real-Time Sync | Polling, Server-Sent Events, WebSocket | **WebSocket** | Bidirectional, low latency, industry standard for real-time apps |
| Notification Channels | Email only, Push only, Email + Push | **Email + Push** | Balanced reliability (email) and immediacy (push), aligns with clarification decision |
| Audit Log Access | Admin only, All users, Admin + own history | **Admin all, users own** | Privacy-preserving, supports accountability, aligns with clarification decision |

## Phase 1: Design & Contracts

### Data Model Extensions

**New Tables:**
- `audit_logs`: event_id (PK), timestamp, user_id, event_type, task_id, payload (JSONB)

**Extended Tables:**
- `tasks`: Add columns for recurring pattern, priority, tags, due_date, reminder_time

**Dapr State Store Keys:**
- `reminder:{task_id}`: Scheduled reminder metadata
- `consumer_offset:{service}:{topic}`: Event processing offsets
- `sequence:{task_id}`: Event sequence numbers

### Event Schemas

**Task Event (task-events topic):**
```json
{
  "specversion": "1.0",
  "type": "com.todo.task.created|updated|completed|deleted",
  "source": "backend-api",
  "id": "uuid",
  "time": "2026-02-09T10:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "task_id": "uuid",
    "user_id": "uuid",
    "sequence": 123,
    "idempotency_key": "uuid",
    "payload": {
      "title": "string",
      "description": "string",
      "status": "pending|completed",
      "priority": "high|medium|low",
      "tags": ["string"],
      "due_date": "2026-02-10T10:00:00Z",
      "recurring_pattern": "daily|weekly|monthly|custom",
      "recurring_interval": 1,
      "changed_fields": ["status", "due_date"]
    }
  }
}
```

**Reminder Event (reminders topic):**
```json
{
  "specversion": "1.0",
  "type": "com.todo.reminder.schedule|cancel",
  "source": "backend-api",
  "id": "uuid",
  "time": "2026-02-09T10:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "task_id": "uuid",
    "user_id": "uuid",
    "due_date": "2026-02-10T10:00:00Z",
    "reminder_time": "2026-02-10T09:45:00Z",
    "notification_channels": ["email", "push"]
  }
}
```

**Task Update Event (task-updates topic):**
```json
{
  "specversion": "1.0",
  "type": "com.todo.task.sync",
  "source": "sync-service",
  "id": "uuid",
  "time": "2026-02-09T10:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "task_id": "uuid",
    "user_id": "uuid",
    "sequence": 123,
    "changed_fields": {
      "status": "completed",
      "updated_at": "2026-02-09T10:00:00Z"
    }
  }
}
```

### API Contracts

**Event Publishing (Internal):**
- POST `/v1.0/publish/{pubsubname}/{topic}` (Dapr HTTP API)
- Headers: `Content-Type: application/cloudevents+json`
- Body: CloudEvents-compliant event payload

**Event Subscription (Dapr):**
- GET `/dapr/subscribe` - Returns subscription configuration
- POST `/events/{topic}` - Receives events from Dapr

**WebSocket (Real-Time Sync):**
- WS `/ws/tasks` - WebSocket connection for task updates
- Authentication: JWT token in query param or header
- Messages: JSON-encoded task update events

**Audit Log Query:**
- GET `/api/audit-logs?user_id={id}&start_date={date}&end_date={date}`
- Response: Paginated list of audit log entries
- Authorization: Admin sees all, users see only own

### Dapr Component Configurations

**pubsub.kafka.yaml:**
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub
spec:
  type: pubsub.kafka
  version: v1
  metadata:
  - name: brokers
    value: "bootstrap.redpanda.cloud:9092"
  - name: authType
    value: "password"
  - name: saslUsername
    secretKeyRef:
      name: redpanda-creds
      key: username
  - name: saslPassword
    secretKeyRef:
      name: redpanda-creds
      key: password
  - name: consumerGroup
    value: "{APP_ID}"
```

**statestore.postgresql.yaml:**
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
spec:
  type: state.postgresql
  version: v1
  metadata:
  - name: connectionString
    secretKeyRef:
      name: postgres-creds
      key: connectionString
  - name: tableName
    value: "dapr_state"
```

**scheduler.yaml:**
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: scheduler
spec:
  type: bindings.cron
  version: v1
  metadata:
  - name: schedule
    value: "@every 1m"
```

**secretstores.kubernetes.yaml:**
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: kubernetes-secrets
spec:
  type: secretstores.kubernetes
  version: v1
  metadata: []
```

## Implementation Phases

### Phase 2A: Event Publishing Infrastructure (Priority: P1)

**Goal**: Extend existing backend to publish task events to Redpanda via Dapr

**Tasks**:
1. Add Dapr SDK to backend requirements.txt
2. Create `backend/events/publisher.py` with Dapr HTTP client
3. Define event schemas in `backend/events/schemas.py`
4. Extend `backend/routers/tasks.py` to publish events on CRUD operations
5. Add idempotency key generation
6. Add event sequence number tracking
7. Create unit tests for event publishing
8. Create integration tests for event flow

**Acceptance Criteria**:
- Task create/update/complete/delete operations publish events to task-events topic
- Events include idempotency keys and sequence numbers
- Events follow CloudEvents specification
- Unit tests verify event payload structure
- Integration tests verify events reach Redpanda

### Phase 2B: Recurring Task Service (Priority: P1)

**Goal**: Build service that consumes task completion events and creates next occurrence

**Tasks**:
1. Create `backend/services/recurring-task/` directory structure
2. Implement Dapr subscription endpoint (`/dapr/subscribe`)
3. Implement event consumer (`/events/task-events`)
4. Implement recurring task logic (calculate next due date)
5. Implement task creation via backend API
6. Add idempotency check to prevent duplicates
7. Add error handling with exponential backoff
8. Create unit tests for recurring logic
9. Create integration tests for end-to-end flow

**Acceptance Criteria**:
- Service subscribes to task-events topic
- On task completion event, creates next occurrence if recurring
- Preserves all task properties (title, description, priority, tags)
- Calculates correct next due date based on pattern (daily, weekly, monthly)
- Prevents duplicate task creation via idempotency keys
- Retries failed operations with exponential backoff (1s, 5s, 25s)
- Moves unrecoverable events to dead-letter queue

### Phase 2C: Notification Service (Priority: P2)

**Goal**: Build service that schedules and sends reminders via email/push

**Tasks**:
1. Create `backend/services/notification/` directory structure
2. Implement Dapr subscription endpoint
3. Implement reminder scheduling via Dapr Jobs API
4. Implement email notifier (SendGrid or SMTP)
5. Implement push notifier (Firebase Cloud Messaging)
6. Add reminder cancellation on task completion
7. Add retry logic for failed notifications
8. Create unit tests for scheduling logic
9. Create integration tests for notification delivery

**Acceptance Criteria**:
- Service subscribes to reminders topic
- Schedules reminders via Dapr Jobs API based on due date
- Sends email notifications to user
- Sends push notifications to user devices
- Cancels scheduled reminders when task completed/deleted
- Retries failed notifications with exponential backoff
- Delivers notifications within 30 seconds of scheduled time

### Phase 2D: Audit Service (Priority: P4)

**Goal**: Build service that logs all task operations to audit trail

**Tasks**:
1. Create `backend/services/audit/` directory structure
2. Create `audit_logs` table in database
3. Implement Dapr subscription endpoint
4. Implement audit log writer
5. Implement audit log query API
6. Add access control (admin all, users own)
7. Add 90-day retention policy
8. Create unit tests for logging logic
9. Create integration tests for audit trail

**Acceptance Criteria**:
- Service subscribes to task-events topic
- Logs all task operations (create, update, complete, delete)
- Records timestamp, user_id, event_type, full payload
- Provides query API with date range filtering
- Enforces access control (admin sees all, users see own)
- Retains logs for 90 days
- 100% reliability (no lost audit entries)

### Phase 2E: Real-Time Sync Service (Priority: P3)

**Goal**: Build service that broadcasts task updates to WebSocket clients

**Tasks**:
1. Create `backend/services/sync/` directory structure
2. Implement WebSocket server with FastAPI
3. Implement connection management (auth, reconnection)
4. Implement Dapr subscription endpoint
5. Implement event broadcasting to connected clients
6. Add event sequence number handling
7. Add client-side gap detection support
8. Create unit tests for broadcasting logic
9. Create integration tests for real-time sync

**Acceptance Criteria**:
- Service subscribes to task-updates topic
- Maintains WebSocket connections with JWT authentication
- Broadcasts task updates to all connected clients for that user
- Includes event sequence numbers in messages
- Clients receive updates within 2 seconds
- Handles reconnection gracefully
- Supports gap detection and missing event requests

### Phase 2F: Frontend Real-Time Updates (Priority: P3)

**Goal**: Extend frontend to receive and display real-time task updates

**Tasks**:
1. Create `frontend/hooks/useWebSocket.ts` hook
2. Create `frontend/services/websocket.ts` client
3. Extend `TaskList.tsx` to handle real-time updates
4. Implement event sequence number tracking
5. Implement gap detection and recovery
6. Add optimistic UI updates
7. Add reconnection logic
8. Create unit tests for WebSocket hook
9. Create E2E tests for real-time sync

**Acceptance Criteria**:
- Frontend connects to WebSocket server with JWT
- Receives task update events in real-time
- Updates UI within 2 seconds of event
- Detects out-of-order events via sequence numbers
- Requests missing events when gaps detected
- Handles reconnection automatically
- Provides smooth UX without disrupting user input

## Testing Strategy

### Unit Tests

**Backend Event Publishing:**
```bash
pytest backend/tests/unit/test_event_publisher.py -v
```
- Test event schema validation
- Test idempotency key generation
- Test sequence number tracking
- Test Dapr HTTP client calls

**Recurring Task Logic:**
```bash
pytest backend/services/recurring-task/tests/test_task_creator.py -v
```
- Test daily recurrence calculation
- Test weekly recurrence calculation
- Test monthly recurrence calculation
- Test end condition handling (never, after N, by date)

**Notification Scheduling:**
```bash
pytest backend/services/notification/tests/test_scheduler.py -v
```
- Test reminder time calculation (15 min before, 1 hour before, etc.)
- Test Dapr Jobs API integration
- Test cancellation logic

### Integration Tests

**Event Flow Tests:**
```bash
pytest backend/tests/integration/test_event_flows.py -v
```
- Test task create → event published → recurring service creates next task
- Test task due date set → reminder scheduled → notification sent
- Test task update → real-time sync → WebSocket clients receive update
- Test task operation → audit log entry created

**Minikube Deployment Test:**
```bash
./scripts/setup-minikube.sh
./scripts/deploy-local.sh
pytest backend/tests/e2e/test_minikube_deployment.py -v
```
- Test all services deploy successfully
- Test Dapr components configured correctly
- Test end-to-end event flows in Kubernetes
- Test health checks pass

### Contract Tests

**Event Schema Validation:**
```bash
pytest backend/tests/contract/test_event_schemas.py -v
```
- Validate task-event schema against CloudEvents spec
- Validate reminder-event schema
- Validate task-update-event schema
- Test schema versioning compatibility

## Risk Mitigation

### Risk 1: Redpanda Cloud Connection Failures

**Impact**: Events cannot be published, system functionality degraded

**Mitigation**:
- Dapr built-in retry with exponential backoff
- Circuit breaker pattern in Dapr configuration
- Event buffering in Dapr sidecar
- Monitoring and alerting on connection failures
- Fallback to local Kafka/Redpanda in Minikube for development

**Detection**: Health check endpoint monitors Dapr Pub/Sub component status

### Risk 2: Event Loss or Duplication

**Impact**: Missing tasks, duplicate notifications, inconsistent state

**Mitigation**:
- Idempotency keys in all events (UUID v4)
- Consumer-side deduplication check before processing
- Dapr consumer group management for at-least-once delivery
- Event replay capability via Dapr
- Audit logs for debugging and recovery

**Detection**: Monitor event processing metrics, audit log completeness

### Risk 3: Dapr Sidecar Crashes

**Impact**: Service cannot publish/consume events, state operations fail

**Mitigation**:
- Kubernetes pod restart policy (Always)
- Dapr sidecar health checks (liveness/readiness probes)
- State persisted in PostgreSQL (survives restarts)
- Event replay on recovery
- Monitoring and alerting on sidecar health

**Detection**: Kubernetes pod status, Dapr health endpoints

### Risk 4: WebSocket Connection Instability

**Impact**: Real-time updates delayed or lost

**Mitigation**:
- Automatic reconnection with exponential backoff
- Event sequence numbers for gap detection
- Missing event request mechanism
- Fallback to polling if WebSocket unavailable
- Connection state monitoring

**Detection**: Client-side connection status, server-side connection metrics

### Risk 5: Notification Delivery Failures

**Impact**: Users miss reminders, reduced task completion rates

**Mitigation**:
- Exponential backoff retry (1s, 5s, 25s)
- Dead-letter queue for unrecoverable failures
- Multiple notification channels (email + push)
- Delivery status tracking in logs
- Manual retry capability for admins

**Detection**: Monitor notification success/failure rates, DLQ depth

### Risk 6: Performance Degradation Under Load

**Impact**: Event processing delays exceed SLA (5s for recurring, 30s for reminders, 2s for sync)

**Mitigation**:
- Horizontal pod autoscaling (HPA) based on CPU/memory
- Kafka consumer group parallelism
- Rate limiting on event publishing
- Batching on event consumption
- Performance testing with 1000 concurrent operations

**Detection**: Monitor event processing latency, queue depth, pod resource usage

### Risk 7: Database Connection Pool Exhaustion

**Impact**: Services cannot read/write state, operations fail

**Mitigation**:
- Configure appropriate connection pool size in Dapr State Store
- Connection timeout and retry settings
- Database connection monitoring
- Graceful degradation (return cached data if available)
- Horizontal scaling of database (Neon autoscaling)

**Detection**: Monitor database connection pool metrics, query latency

## Next Steps

1. ✅ **Phase 0 Complete**: Research topics identified, decisions documented
2. 🔄 **Phase 1 In Progress**: Generate research.md, data-model.md, contracts/, quickstart.md
3. ⏳ **Phase 2 Pending**: Run `/sp.tasks` to generate tasks.md with implementation steps
4. ⏳ **Phase 3 Pending**: Execute tasks via `/sp.implement`

**Ready for**: Phase 1 artifact generation (research.md, data-model.md, contracts/, quickstart.md)

