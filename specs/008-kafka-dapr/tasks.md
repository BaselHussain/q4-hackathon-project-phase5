# Tasks: Kafka + Dapr Event-Driven Architecture

**Input**: Design documents from `/specs/008-kafka-dapr/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/`, `frontend/`
- **Microservices**: `backend/services/recurring-task/`, `backend/services/notification/`, etc.
- **Dapr components**: `dapr-components/`
- **Helm charts**: `helm/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dual configuration setup (Minikube + Redpanda, OKE + Oracle Streaming)

### Message Broker Setup (Dual Configuration)

**For Minikube (Local Development):**
- [x] T001a Set up Redpanda (local or Redpanda Cloud) for Minikube
- [x] T002a Create Redpanda topics: task-events (3 partitions), reminders (1 partition), task-updates (3 partitions)
- [x] T003a Store Redpanda credentials in backend/.env (REDPANDA_BOOTSTRAP_SERVERS, REDPANDA_SASL_USERNAME, REDPANDA_SASL_PASSWORD)

**For OKE (Production Deployment):**
- [x] T001b Set up Oracle Streaming Service (see docs/ORACLE_CLOUD_SETUP.md)
- [x] T002b Create Oracle Streaming streams: task-events (3 partitions), reminders (1 partition), task-updates (3 partitions)
- [x] T003b Store Oracle Streaming credentials in backend/.env (ORACLE_STREAMING_ENDPOINT, ORACLE_STREAMING_USERNAME, ORACLE_STREAMING_AUTH_TOKEN)

### Common Setup
- [x] T004 [P] Install Dapr CLI 1.12+ locally (dapr init)
- [x] T005 [P] Verify Dapr installation (dapr --version, docker ps | grep dapr)
- [x] T006 Create dapr-components/ directory structure
- [x] T007 [P] Add dapr==1.12.0 to backend/requirements.txt
- [x] T008 [P] Add httpx==0.26.0 to backend/requirements.txt
- [x] T009 [P] Add croniter to backend/requirements.txt for recurring date calculations
- [x] T010 [P] Add websockets to backend/requirements.txt for real-time sync

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core event publishing infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database Migration

- [x] T011 Create backend/migrate_event_architecture.py with audit_logs table schema
- [x] T012 Create backend/migrate_event_architecture.py with dapr_state table schema
- [x] T013 Run database migration script (python backend/migrate_event_architecture.py)
- [x] T014 Verify audit_logs table created with indexes (id, event_id, user_id, timestamp, event_type, task_id)
- [x] T015 Verify dapr_state table created with indexes (key, updatedate)

### Dapr Component Configuration (Dual Configuration)

**For Minikube (Local Development):**
- [x] T016a [P] Create dapr-components/pubsub.kafka.minikube.yaml with Redpanda configuration (SCRAM-SHA-256, redpanda-creds secret)

**For OKE (Production Deployment):**
- [x] T016b [P] Create dapr-components/pubsub.kafka.oke.yaml with Oracle Streaming configuration (PLAIN SASL, oci-streaming-creds secret)

**Common Components:**
- [x] T017 [P] Create dapr-components/statestore.postgresql.yaml with Neon connection string
- [x] T018 [P] Create dapr-components/secretstores.kubernetes.yaml for Kubernetes secrets
- [x] T019 Copy Dapr components to ~/.dapr/components/ for local development (use pubsub.kafka.minikube.yaml)
- [x] T020 Verify Dapr components loaded (dapr components -k)

### Event Publishing Infrastructure

- [x] T021 Create backend/events/ directory
- [x] T022 Create backend/events/schemas.py with CloudEvents-compliant event structures
- [x] T023 Create backend/events/publisher.py with publish_event() function using Dapr HTTP API
- [x] T024 Add idempotency key generation (UUID v4) to publisher.py
- [x] T025 Add event sequence number tracking to publisher.py
- [x] T026 Create backend/tests/unit/test_event_publisher.py with schema validation tests
- [x] T027 Create backend/tests/integration/test_event_flows.py skeleton

### Extend Task Router with Event Publishing

- [x] T028 Import publish_event in backend/routers/tasks.py
- [x] T029 Add event publishing to create_task() endpoint (com.todo.task.created)
- [x] T030 Add event publishing to update_task() endpoint (com.todo.task.updated)
- [x] T031 Add event publishing to complete_task() endpoint (com.todo.task.completed)
- [x] T032 Add event publishing to delete_task() endpoint (com.todo.task.deleted)
- [x] T033 Add error handling for event publishing failures (log but don't block request)
- [x] T034 Test event publishing locally (dapr run --app-id backend-api --app-port 8000 --dapr-http-port 3500 -- uvicorn app.main:app)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automatic Recurring Task Creation (Priority: P1) 🎯 MVP

**Goal**: When a user completes a recurring task, the system automatically creates the next occurrence without manual intervention

**Independent Test**: Create a recurring task (e.g., "Weekly team meeting"), mark it complete, and verify the next occurrence is automatically created with the correct due date

### Service Structure

- [x] T035 [P] [US1] Create backend/services/recurring-task/ directory
- [x] T036 [P] [US1] Create backend/services/recurring-task/main.py with FastAPI app
- [x] T037 [P] [US1] Create backend/services/recurring-task/consumer.py for event consumption
- [x] T038 [P] [US1] Create backend/services/recurring-task/task_creator.py for task creation logic
- [x] T039 [P] [US1] Create backend/services/recurring-task/requirements.txt

### Dapr Subscription

- [x] T040 [US1] Implement /dapr/subscribe endpoint in main.py returning subscription config for task-events topic
- [x] T041 [US1] Implement /events/task-events POST endpoint to receive events from Dapr
- [x] T042 [US1] Add JWT service token generation for calling backend API

### Recurring Task Logic

- [x] T043 [US1] Implement calculate_next_due_date() in task_creator.py for daily recurrence
- [x] T044 [US1] Implement calculate_next_due_date() in task_creator.py for weekly recurrence
- [x] T045 [US1] Implement calculate_next_due_date() in task_creator.py for monthly recurrence
- [x] T046 [US1] Implement create_next_task_occurrence() in task_creator.py calling backend API
- [x] T047 [US1] Add idempotency check using event ID to prevent duplicate task creation
- [x] T048 [US1] Add error handling with exponential backoff retry (1s, 5s, 25s)

### Testing

- [x] T049 [US1] Create backend/services/recurring-task/tests/test_task_creator.py with unit tests
- [x] T050 [US1] Test daily recurrence calculation (today + 1 day)
- [x] T051 [US1] Test weekly recurrence calculation (today + 7 days)
- [x] T052 [US1] Test monthly recurrence calculation (today + 30 days)
- [x] T053 [US1] Add integration test in backend/tests/integration/test_event_flows.py for recurring task flow
- [x] T054 [US1] Run recurring task service with Dapr (dapr run --app-id recurring-task-service --app-port 8001 --dapr-http-port 3501 -- python main.py)
- [x] T055 [US1] Test end-to-end: create recurring task → complete → verify next occurrence created

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Timely Task Reminders (Priority: P2)

**Goal**: When a user sets a due date on a task, the system automatically schedules and sends a reminder notification at the appropriate time

**Independent Test**: Create a task with a due date 5 minutes in the future, wait for the reminder time, and verify a notification is received

### Service Structure

- [x] T056 [P] [US2] Create backend/services/notification/ directory
- [x] T057 [P] [US2] Create backend/services/notification/main.py with FastAPI app
- [x] T058 [P] [US2] Create backend/services/notification/consumer.py for event consumption
- [x] T059 [P] [US2] Create backend/services/notification/scheduler.py for Dapr Jobs API integration
- [x] T060 [P] [US2] Create backend/services/notification/notifiers/ directory
- [x] T061 [P] [US2] Create backend/services/notification/requirements.txt

### Dapr Subscription

- [x] T062 [US2] Implement /dapr/subscribe endpoint in main.py returning subscription config for reminders topic
- [x] T063 [US2] Implement /events/reminders POST endpoint to receive reminder events from Dapr
- [x] T064 [US2] Extend backend/routers/tasks.py to publish reminder.schedule event when due date set
- [x] T065 [US2] Extend backend/routers/tasks.py to publish reminder.cancel event when task completed/deleted

### Reminder Scheduling

- [x] T066 [US2] Implement schedule_reminder() in scheduler.py using Dapr Jobs API (POST /v1.0-alpha1/jobs/{jobName})
- [x] T067 [US2] Implement cancel_reminder() in scheduler.py using Dapr Jobs API (DELETE /v1.0-alpha1/jobs/{jobName})
- [x] T068 [US2] Implement /jobs/reminder-{task_id} POST endpoint to receive job callbacks from Dapr
- [x] T069 [US2] Calculate reminder time (15 minutes before due date by default)
- [x] T070 [US2] Store scheduled reminder metadata in Dapr State Store (key: reminder:{task_id})

### Email Notifier

- [x] T071 [P] [US2] Create backend/services/notification/notifiers/email.py
- [x] T072 [P] [US2] Implement send_email() using SendGrid API or SMTP
- [x] T073 [P] [US2] Add email template for task reminder
- [x] T074 [P] [US2] Add SENDGRID_API_KEY to backend/.env

### Push Notifier

- [x] T075 [P] [US2] Create backend/services/notification/notifiers/push.py
- [x] T076 [P] [US2] Implement send_push() using Firebase Cloud Messaging
- [x] T077 [P] [US2] Add FCM_SERVER_KEY to backend/.env
- [x] T078 [P] [US2] Add retry logic for failed notifications (exponential backoff)

### Testing

- [x] T079 [US2] Create backend/services/notification/tests/test_scheduler.py with unit tests
- [x] T080 [US2] Test reminder time calculation (due_date - 15 minutes)
- [x] T081 [US2] Test Dapr Jobs API integration (schedule, cancel)
- [x] T082 [US2] Add integration test in backend/tests/integration/test_event_flows.py for notification flow
- [x] T083 [US2] Run notification service with Dapr (dapr run --app-id notification-service --app-port 8002 --dapr-http-port 3502 -- python main.py)
- [x] T084 [US2] Test end-to-end: create task with due date → verify reminder scheduled → verify notification sent

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Real-Time Task Synchronization (Priority: P3)

**Goal**: When a user updates a task on one device, all other connected clients immediately see the changes without manual refresh

**Independent Test**: Open the todo app on two devices, update a task on device A, and verify device B shows the change within 2 seconds

### Backend Real-Time Sync Service

- [x] T085 [P] [US3] Create backend/services/sync/ directory
- [x] T086 [P] [US3] Create backend/services/sync/main.py with FastAPI app
- [x] T087 [P] [US3] Create backend/services/sync/consumer.py for event consumption
- [x] T088 [P] [US3] Create backend/services/sync/websocket.py for WebSocket server
- [x] T089 [P] [US3] Create backend/services/sync/requirements.txt

### Dapr Subscription

- [x] T090 [US3] Implement /dapr/subscribe endpoint in main.py returning subscription config for task-updates topic
- [x] T091 [US3] Implement /events/task-updates POST endpoint to receive task update events from Dapr
- [x] T092 [US3] Extend backend/routers/tasks.py to publish task.sync event on all task updates

### WebSocket Server

- [x] T093 [US3] Implement /ws/tasks WebSocket endpoint in websocket.py
- [x] T094 [US3] Add JWT authentication for WebSocket connections (token in query param or header)
- [x] T095 [US3] Implement connection manager to track connected clients by user_id
- [x] T096 [US3] Implement broadcast_to_user() to send updates to all user's connected clients
- [x] T097 [US3] Add event sequence number handling in messages
- [x] T098 [US3] Add reconnection support with gap detection

### Testing

- [x] T099 [US3] Create backend/services/sync/tests/test_websocket.py with unit tests
- [x] T100 [US3] Test WebSocket authentication
- [x] T101 [US3] Test message broadcasting to multiple clients
- [x] T102 [US3] Add integration test in backend/tests/integration/test_event_flows.py for real-time sync
- [x] T103 [US3] Run sync service with Dapr (dapr run --app-id sync-service --app-port 8003 --dapr-http-port 3503 -- python main.py)

### Frontend WebSocket Client

- [x] T104 [P] [US3] Create frontend/hooks/useWebSocket.ts hook
- [x] T105 [P] [US3] Create frontend/services/websocket.ts client
- [x] T106 [US3] Implement WebSocket connection with JWT token
- [x] T107 [US3] Implement automatic reconnection with exponential backoff
- [x] T108 [US3] Implement event sequence number tracking
- [x] T109 [US3] Implement gap detection and missing event request
- [x] T110 [US3] Extend frontend/components/TaskList.tsx to use useWebSocket hook
- [x] T111 [US3] Add optimistic UI updates for task operations
- [x] T112 [US3] Test real-time sync: open two browser tabs, update task in tab 1, verify tab 2 updates

**Checkpoint**: All user stories 1, 2, and 3 should now be independently functional

---

## Phase 6: User Story 4 - Comprehensive Audit Trail (Priority: P4)

**Goal**: All task operations (create, update, complete, delete) are automatically logged with timestamp and user information

**Independent Test**: Perform various task operations (create, update, delete) and verify all actions are logged with correct timestamps and user IDs

### Service Structure

- [x] T113 [P] [US4] Create backend/services/audit/ directory
- [x] T114 [P] [US4] Create backend/services/audit/main.py with FastAPI app
- [x] T115 [P] [US4] Create backend/services/audit/consumer.py for event consumption
- [x] T116 [P] [US4] Create backend/services/audit/logger.py for audit log writing
- [x] T117 [P] [US4] Create backend/services/audit/requirements.txt

### Dapr Subscription

- [x] T118 [US4] Implement /dapr/subscribe endpoint in main.py returning subscription config for task-events topic
- [x] T119 [US4] Implement /events/task-events POST endpoint to receive all task events from Dapr

### Audit Log Writer

- [x] T120 [US4] Implement write_audit_log() in logger.py to insert into audit_logs table
- [x] T121 [US4] Record event_id, timestamp, user_id, event_type, task_id, payload (JSONB)
- [x] T122 [US4] Add idempotency check using event_id to prevent duplicate log entries
- [x] T123 [US4] Add error handling with retry for database failures

### Audit Log Query API

- [x] T124 [US4] Create backend/routers/audit.py with GET /api/audit-logs endpoint
- [x] T125 [US4] Add query parameters: user_id, start_date, end_date, event_type
- [x] T126 [US4] Implement pagination (limit, offset)
- [x] T127 [US4] Add access control: admin sees all logs, users see only their own
- [x] T128 [US4] Add 90-day retention policy (cleanup job or TTL)

### Testing

- [x] T129 [US4] Create backend/services/audit/tests/test_logger.py with unit tests
- [x] T130 [US4] Test audit log writing for all event types
- [x] T131 [US4] Test idempotency (duplicate event_id should not create duplicate log)
- [x] T132 [US4] Add integration test in backend/tests/integration/test_event_flows.py for audit trail
- [x] T133 [US4] Run audit service with Dapr (dapr run --app-id audit-service --app-port 8004 --dapr-http-port 3504 -- python main.py)
- [x] T134 [US4] Test end-to-end: perform task operations → verify audit logs created → query audit logs API

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### Kubernetes Deployment

- [x] T135 [P] Create helm/backend/ Helm chart with Dapr sidecar annotations
- [x] T136 [P] Create helm/recurring-task/ Helm chart with Dapr sidecar annotations
- [x] T137 [P] Create helm/notification/ Helm chart with Dapr sidecar annotations
- [x] T138 [P] Create helm/sync/ Helm chart with Dapr sidecar annotations
- [x] T139 [P] Create helm/audit/ Helm chart with Dapr sidecar annotations
- [x] T140 Create scripts/setup-minikube.sh for local Kubernetes setup
- [x] T141 Create scripts/deploy-local.sh for deploying all services to Minikube
- [x] T142 Test Minikube deployment (./scripts/setup-minikube.sh && ./scripts/deploy-local.sh)

### CI/CD Pipeline

- [x] T143 [P] Create .github/workflows/build-test.yml for building and testing
- [x] T144 [P] Create .github/workflows/deploy-staging.yml for staging deployment
- [x] T145 [P] Create .github/workflows/deploy-production.yml for production deployment
- [x] T146 Add Minikube integration tests to CI pipeline

### Documentation

- [x] T147 [P] Update README.md with Kafka + Dapr architecture overview
- [x] T148 [P] Update README.md with local development setup instructions
- [x] T149 [P] Update README.md with deployment instructions
- [x] T150 [P] Create architecture diagram showing event flows between services
- [x] T151 Validate quickstart.md instructions (follow step-by-step and verify)

### Contract Tests

- [x] T152 [P] Create backend/tests/contract/test_event_schemas.py
- [x] T153 [P] Validate task-event schema against CloudEvents spec
- [x] T154 [P] Validate reminder-event schema against CloudEvents spec
- [x] T155 [P] Validate task-update-event schema against CloudEvents spec

### Performance & Monitoring

- [x] T156 [P] Add health check endpoints to all services
- [x] T157 [P] Add Prometheus metrics for event processing latency
- [x] T158 [P] Add logging for all event publishing and consumption
- [x] T159 Test performance: 1000 concurrent task operations without event loss

### Security Hardening

- [x] T160 [P] Verify all Dapr components use Kubernetes secrets for credentials
- [x] T161 [P] Verify JWT authentication on all WebSocket connections
- [x] T162 [P] Verify audit log access control (admin all, users own)
- [x] T163 Review all services for security vulnerabilities

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User Story 1 (P1): Can start after Foundational - No dependencies on other stories
  - User Story 2 (P2): Can start after Foundational - No dependencies on other stories
  - User Story 3 (P3): Can start after Foundational - No dependencies on other stories
  - User Story 4 (P4): Can start after Foundational - No dependencies on other stories
  - User stories can proceed in parallel (if staffed) or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### Within Each User Story

- Service structure before Dapr subscription
- Dapr subscription before business logic
- Business logic before testing
- Unit tests before integration tests
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Within each user story, tasks marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Recurring Task Service)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (P1) - Recurring Task Service
   - Developer B: User Story 2 (P2) - Notification Service
   - Developer C: User Story 3 (P3) - Real-Time Sync Service
   - Developer D: User Story 4 (P4) - Audit Service
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- All services use Dapr for messaging (no direct Kafka clients)
- All services use Dapr State Store for persistence (no direct Redis/database state)
- All events follow CloudEvents 1.0 specification
- All services include idempotency checks to prevent duplicate processing
- All services include exponential backoff retry (1s, 5s, 25s) with dead-letter queue

---

## ✅ Implementation Status: COMPLETED

**All 163 tasks completed successfully!**

### Phase Completion Summary

- ✅ **Phase 1: Setup** - Dual configuration (Minikube + Redpanda, OKE + Oracle Streaming)
- ✅ **Phase 2: Foundational** - Event publishing infrastructure, Dapr components, database migration
- ✅ **Phase 3: User Story 1** - Recurring Task Service (automatic next occurrence creation)
- ✅ **Phase 4: User Story 2** - Notification Service (email + push reminders via Dapr Jobs API)
- ✅ **Phase 5: User Story 3** - Real-Time Sync Service (WebSocket with JWT auth)
- ✅ **Phase 6: User Story 4** - Audit Service (comprehensive audit trail)
- ✅ **Phase 7: Polish** - Helm charts, CI/CD, documentation, security hardening

---

## 🎯 Dual Configuration Approach (Phase 5 Compliance)

To meet Phase 5 requirements for both local development and production deployment, we implemented a **dual configuration approach**:

### Configuration 1: Minikube (Local Development)
- **Message Broker**: Redpanda (Kafka-compatible)
- **Dapr Component**: `dapr-components/pubsub.kafka.minikube.yaml`
- **SASL Mechanism**: SCRAM-SHA-256
- **Kubernetes Secret**: `redpanda-creds`
- **Setup Script**: `./scripts/setup-minikube.sh`
- **Use Case**: Local development, testing, CI/CD

### Configuration 2: OKE (Production Deployment)
- **Message Broker**: Oracle Streaming Service (Kafka-compatible)
- **Dapr Component**: `dapr-components/pubsub.kafka.oke.yaml`
- **SASL Mechanism**: PLAIN
- **Kubernetes Secret**: `oci-streaming-creds`
- **Setup Guide**: `docs/ORACLE_CLOUD_SETUP.md`
- **Use Case**: Production deployment on Oracle Cloud Infrastructure

### Additional Work Completed (Beyond Original Tasks)

- [x] T164 Create `dapr-components/pubsub.kafka.minikube.yaml` for Redpanda configuration
- [x] T165 Rename `pubsub.kafka.yaml` to `pubsub.kafka.oke.yaml` for Oracle Streaming
- [x] T166 Update `backend/.env` to include both Redpanda and Oracle Streaming credentials
- [x] T167 Update `scripts/setup-minikube.sh` to use Minikube-specific Dapr component
- [x] T168 Update `scripts/setup-minikube.sh` to create `redpanda-creds` secret
- [x] T169 Update `docs/ORACLE_CLOUD_SETUP.md` to reference `pubsub.kafka.oke.yaml`
- [x] T170 Create `docs/DEPLOYMENT_GUIDE.md` comparing both deployment options
- [x] T171 Update `docs/ORACLE_CLOUD_MIGRATION.md` with dual configuration approach
- [x] T172 Update `README.md` Technology Stack section for dual configuration
- [x] T173 Update `README.md` deployment sections with both options
- [x] T174 Update all Redpanda references in operational files to reflect dual approach

---

## 📚 Documentation Created

### Deployment Documentation
- **`docs/DEPLOYMENT_GUIDE.md`** - Comprehensive guide comparing Minikube vs OKE deployment
- **`docs/ORACLE_CLOUD_SETUP.md`** - Step-by-step OKE deployment with exact OCI CLI commands
- **`docs/ORACLE_CLOUD_MIGRATION.md`** - Dual configuration approach and migration checklists
- **`README.md`** - Updated with dual configuration explanation and quick start guides

### Architecture Documentation
- Event flow diagrams
- Service interaction patterns
- CloudEvents 1.0 schema specifications
- Dapr component configurations

---

## 🚀 Deployment Paths

### Path 1: Local Development (Minikube)
```bash
# 1. Configure Redpanda in .env
# 2. Run setup script
./scripts/setup-minikube.sh

# 3. Deploy services
./scripts/deploy-local.sh

# 4. Access services
kubectl port-forward svc/backend 8000:8000
```

### Path 2: Production (OKE)
```bash
# Follow comprehensive guide
# See: docs/ORACLE_CLOUD_SETUP.md

# Key steps:
# 1. Create Oracle Streaming Service
# 2. Create OKE cluster
# 3. Deploy via Helm with OCIR images
# 4. Configure OCI Native Ingress
```

---

## ✅ Phase 5 Requirements Verification

| Requirement | Status | Evidence |
|------------|--------|----------|
| Kafka-compatible broker | ✅ | Redpanda (Minikube) + Oracle Streaming (OKE) |
| Local development (Minikube) | ✅ | `./scripts/setup-minikube.sh` |
| Cloud deployment (OKE) | ✅ | `docs/ORACLE_CLOUD_SETUP.md` |
| Dapr service mesh | ✅ | Pub/Sub, State Store, Jobs API |
| Event-driven architecture | ✅ | 4 microservices implemented |
| Helm charts | ✅ | All 5 services packaged |
| CI/CD pipelines | ✅ | GitHub Actions workflows |

**Result: Fully aligned with Phase 5 requirements!** ✅

