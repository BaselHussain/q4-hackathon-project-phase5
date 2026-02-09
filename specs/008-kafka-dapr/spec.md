# Feature Specification: Kafka + Dapr Event-Driven Architecture

**Feature Branch**: `008-kafka-dapr`
**Created**: 2026-02-09
**Status**: Draft
**Input**: User description: "Spec 8 - Kafka + Dapr Event-Driven Architecture - Add event-driven architecture using Kafka (or Redpanda) and full Dapr integration for decoupled, scalable todo features in Phase 5."

## Clarifications

### Session 2026-02-09

- Q: Notification channels for task reminders → A: Email + Push notifications
- Q: Message broker selection (Kafka vs Redpanda) → A: Redpanda Cloud serverless free tier
- Q: Event ordering strategy for real-time sync → A: Event sequence numbers with client-side conflict resolution
- Q: Retry strategy for failed event processing → A: Exponential backoff with 3 retries, then dead-letter queue
- Q: Audit log access control → A: Administrators see all logs, users see only their own task history

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic Recurring Task Creation (Priority: P1)

When a user completes a recurring task, the system automatically creates the next occurrence without manual intervention, ensuring continuity of recurring workflows.

**Why this priority**: This is the core value proposition of event-driven architecture - decoupled, automated task management that scales independently. It directly impacts user productivity by eliminating manual task recreation.

**Independent Test**: Can be fully tested by creating a recurring task (e.g., "Weekly team meeting"), marking it complete, and verifying the next occurrence is automatically created with the correct due date. Delivers immediate value by automating repetitive task management.

**Acceptance Scenarios**:

1. **Given** a user has a daily recurring task "Review emails", **When** they mark it complete, **Then** a new task "Review emails" is created with tomorrow's date
2. **Given** a user has a weekly recurring task "Submit timesheet" due Friday, **When** they complete it on Thursday, **Then** a new task is created for next Friday
3. **Given** a user completes a recurring task, **When** the system creates the next occurrence, **Then** all task properties (title, description, priority, tags) are preserved
4. **Given** a recurring task creation fails, **When** the system retries, **Then** duplicate tasks are not created

---

### User Story 2 - Timely Task Reminders (Priority: P2)

When a user sets a due date on a task, the system automatically schedules and sends a reminder notification at the appropriate time, helping users stay on track without manual calendar management.

**Why this priority**: Reminders are critical for task completion rates and user satisfaction. This builds on P1 by adding time-based automation, but is secondary to the core recurring task functionality.

**Independent Test**: Can be fully tested by creating a task with a due date 5 minutes in the future, waiting for the reminder time, and verifying a notification is received. Delivers value by reducing missed deadlines.

**Acceptance Scenarios**:

1. **Given** a user creates a task with due date "2026-02-10 10:00 AM", **When** the reminder time arrives (e.g., 15 minutes before), **Then** the user receives a notification
2. **Given** a user updates a task's due date, **When** the new due date is saved, **Then** the old reminder is cancelled and a new reminder is scheduled
3. **Given** a user completes a task before the reminder time, **When** the task is marked complete, **Then** the scheduled reminder is cancelled
4. **Given** a reminder notification fails to send, **When** the system retries, **Then** the user receives the notification without duplicates

---

### User Story 3 - Real-Time Task Synchronization (Priority: P3)

When a user updates a task on one device or through the chat interface, all other connected clients immediately see the changes without manual refresh, providing a seamless multi-device experience.

**Why this priority**: Real-time sync enhances user experience but is not critical for core functionality. Users can still work effectively with manual refresh. This is a polish feature that improves perceived responsiveness.

**Independent Test**: Can be fully tested by opening the todo app on two devices, updating a task on device A, and verifying device B shows the change within 2 seconds. Delivers value by eliminating confusion from stale data.

**Acceptance Scenarios**:

1. **Given** a user has the todo app open on desktop and mobile, **When** they update a task title on desktop, **Then** the mobile app shows the updated title within 2 seconds
2. **Given** multiple users share a task list, **When** one user marks a task complete, **Then** all other users see the completion status update in real-time
3. **Given** a user is offline, **When** they make task changes, **Then** changes are queued and synchronized when connection is restored
4. **Given** a task update event is received, **When** the user is viewing that task, **Then** the UI updates smoothly without disrupting user input

---

### User Story 4 - Comprehensive Audit Trail (Priority: P4)

All task operations (create, update, complete, delete) are automatically logged with timestamp and user information, providing accountability and debugging capabilities for team workflows.

**Why this priority**: Audit logging is important for compliance and debugging but doesn't directly impact day-to-day user experience. It's a foundational capability that supports other features but isn't user-facing.

**Independent Test**: Can be fully tested by performing various task operations (create, update, delete) and verifying all actions are logged with correct timestamps and user IDs. Delivers value for team administrators and compliance requirements.

**Acceptance Scenarios**:

1. **Given** a user creates a new task, **When** the task is saved, **Then** an audit log entry records the creation with timestamp, user ID, and task details
2. **Given** a user updates a task's priority, **When** the update is saved, **Then** an audit log entry records the old and new priority values
3. **Given** a user deletes a task, **When** the deletion is confirmed, **Then** an audit log entry records the deletion with full task snapshot
4. **Given** an administrator views audit logs, **When** they filter by date range, **Then** all task events within that range are displayed in chronological order

---

### Edge Cases

- What happens when a recurring task service is down and misses a task completion event? (Event replay mechanism via Dapr)
- How does the system handle reminder scheduling for tasks with due dates in the past? (Skip past reminders, only schedule future ones)
- What happens when multiple task update events arrive out of order? (Clients use sequence numbers to detect gaps and request missing events)
- How does the system handle notification delivery failures? (Exponential backoff retry: 1s, 5s, 25s, then dead-letter queue)
- What happens when a user creates 1000 recurring tasks and completes them all at once? (Rate limiting on event publishing, batching on consumption)
- How does the system handle clock skew between services? (Use event timestamps from source, not processing time)
- What happens when Redpanda is temporarily unavailable? (Event buffering in Dapr, circuit breaker pattern)
- How does the system handle duplicate events? (Idempotency keys in event payload, deduplication in consumers)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST publish an event when a task is created, containing task ID, user ID, task details, and timestamp
- **FR-002**: System MUST publish an event when a task is updated, containing task ID, user ID, changed fields, and timestamp
- **FR-003**: System MUST publish an event when a task is completed, containing task ID, user ID, completion timestamp, and recurrence information
- **FR-004**: System MUST publish an event when a task is deleted, containing task ID, user ID, and deletion timestamp
- **FR-005**: System MUST publish an event when a task due date is set or updated, containing task ID, user ID, due date, and reminder preferences
- **FR-006**: Recurring Task Service MUST consume task completion events and automatically create the next occurrence for recurring tasks
- **FR-007**: Recurring Task Service MUST preserve all task properties (title, description, priority, tags, recurrence pattern) when creating next occurrence
- **FR-008**: Recurring Task Service MUST calculate the next due date based on recurrence pattern (daily, weekly, monthly, custom)
- **FR-009**: Notification Service MUST consume reminder events and send notifications to users via email and push notifications
- **FR-010**: Notification Service MUST schedule reminders based on user preferences (e.g., 15 minutes before, 1 hour before, 1 day before)
- **FR-011**: Notification Service MUST cancel scheduled reminders when tasks are completed or deleted
- **FR-012**: Audit Service MUST consume all task events and persist them to a durable audit log
- **FR-013**: Audit Service MUST record timestamp, user ID, event type, and full event payload for each audit entry
- **FR-023**: System MUST restrict audit log access so administrators can view all logs while users can only view their own task history
- **FR-014**: System MUST broadcast task update events to all connected clients for real-time synchronization, including event sequence numbers for ordering
- **FR-015**: System MUST ensure events are processed exactly once (idempotency) to prevent duplicate task creation or notifications
- **FR-016**: System MUST handle event processing failures with automatic retry using exponential backoff (1s, 5s, 25s delays) for up to 3 attempts, then move unrecoverable events to dead-letter queue
- **FR-017**: System MUST support event replay for recovering from service outages or data inconsistencies
- **FR-018**: All services MUST communicate via event-driven messaging, not direct API calls, to maintain loose coupling
- **FR-019**: System MUST store service state (e.g., scheduled reminders, processing offsets) in a durable state store
- **FR-020**: System MUST secure event topics and state stores with authentication and authorization
- **FR-021**: Clients MUST detect out-of-order events using sequence numbers and request missing events when gaps are detected
- **FR-022**: System MUST resolve concurrent task updates using last-write-wins strategy based on event timestamps

### Key Entities

- **Task Event**: Represents a state change in a task's lifecycle (created, updated, completed, deleted). Contains task ID, user ID, event type, timestamp, and event-specific payload (e.g., changed fields for updates, recurrence info for completions).

- **Reminder Event**: Represents a scheduled reminder for a task with a due date. Contains task ID, user ID, due date, reminder time, and notification preferences.

- **Task Update Event**: Represents a real-time synchronization message for task changes. Contains task ID, changed fields, and timestamp for broadcasting to connected clients.

- **Audit Log Entry**: Represents a permanent record of a task operation. Contains event ID, timestamp, user ID, event type, task ID, and full event payload for compliance and debugging.

- **Recurring Task Pattern**: Represents the recurrence configuration for a task. Contains recurrence type (daily, weekly, monthly, custom), interval, end condition (never, after N occurrences, by date), and preserved task properties.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: When a user completes a recurring task, the next occurrence is created within 5 seconds
- **SC-002**: When a user sets a task due date, a reminder notification is delivered within 30 seconds of the scheduled reminder time
- **SC-003**: When a user updates a task, all connected clients receive the update within 2 seconds
- **SC-004**: All task operations (create, update, complete, delete) are logged in the audit trail with 100% reliability
- **SC-005**: System handles 1000 concurrent task operations without event loss or processing delays exceeding 10 seconds
- **SC-006**: Event processing failures are automatically retried with 99.9% eventual success rate
- **SC-007**: System recovers from service outages without data loss or duplicate task creation
- **SC-008**: Users report 90% satisfaction with recurring task automation (eliminates manual task recreation)
- **SC-009**: Task completion rates improve by 25% due to timely reminder notifications
- **SC-010**: Support tickets related to "missing tasks" or "duplicate tasks" reduce by 80%

## Assumptions

- Users have already configured notification preferences (email, push, etc.) in their profile settings (from previous features)
- The existing backend (Phase 2/3) provides REST APIs for task CRUD operations that can be extended to publish events
- The existing frontend (Phase 3) supports WebSocket or Server-Sent Events for real-time updates
- Users understand recurring task patterns (daily, weekly, monthly) from common calendar applications
- The system has access to a message broker (Kafka or Redpanda) for event streaming
- The system has access to a distributed runtime (Dapr) for pub/sub, state management, and scheduling
- The system runs in a container orchestration platform (Kubernetes) for deploying multiple services
- Default reminder time is 15 minutes before due date unless user specifies otherwise
- Recurring tasks default to "never end" unless user specifies an end condition
- Audit logs are retained for 90 days for compliance purposes
- Notification delivery is best-effort (retries on failure but may not guarantee delivery for all channels)

## Dependencies

- **Existing Backend API (Phase 2/3)**: Task CRUD operations must be extended to publish events after database writes
- **Existing Frontend (Phase 3)**: Must support real-time updates via WebSocket or Server-Sent Events
- **Advanced Todo Features (Spec 7)**: Recurring task and reminder data models must be available
- **Message Broker**: Redpanda Cloud serverless free tier must be provisioned and accessible (Kafka-compatible)
- **Distributed Runtime**: Dapr must be installed and configured in the deployment environment
- **Container Orchestration**: Kubernetes cluster must be available for deploying microservices
- **Notification Infrastructure**: Email/push notification services must be configured for Notification Service
- **State Store**: PostgreSQL database (existing Neon DB) must be accessible for Dapr state management

## Out of Scope

- Custom notification channels beyond standard email/push (e.g., SMS, Slack, Teams)
- Advanced event analytics or business intelligence dashboards
- Event schema versioning and migration strategies (assume single schema version for MVP)
- Multi-region event replication or geo-distributed deployments
- Custom recurrence patterns beyond daily/weekly/monthly (e.g., "every 3rd Tuesday")
- User-configurable event routing or filtering rules
- Event-driven workflows beyond task lifecycle (e.g., approval workflows, escalations)
- Performance optimization for extremely high throughput (>10,000 events/second)
- Integration with external calendar systems (Google Calendar, Outlook)
- Notification delivery status tracking and read receipts
