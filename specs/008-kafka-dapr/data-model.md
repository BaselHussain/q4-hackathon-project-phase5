# Data Model: Kafka + Dapr Event-Driven Architecture

**Feature**: 008-kafka-dapr
**Date**: 2026-02-09
**Status**: Complete

## Overview

This document defines the data model extensions for event-driven architecture, including database schema changes, event payload structures, and Dapr state store key patterns.

## Database Schema Extensions

### Existing Tables (Extended)

**tasks** (from Spec 7 - Advanced Todo Features)
- Existing columns preserved
- No additional columns needed for event-driven architecture
- Events reference task_id as foreign key

### New Tables

#### audit_logs

Stores comprehensive audit trail of all task operations for compliance and debugging.

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL UNIQUE,  -- Idempotency key from event
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id UUID NOT NULL REFERENCES users(id),
    event_type VARCHAR(50) NOT NULL,  -- task.created, task.updated, etc.
    task_id UUID REFERENCES tasks(id),
    payload JSONB NOT NULL,  -- Full event payload
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Indexes for query performance
    INDEX idx_audit_logs_user_id (user_id),
    INDEX idx_audit_logs_timestamp (timestamp),
    INDEX idx_audit_logs_event_type (event_type),
    INDEX idx_audit_logs_task_id (task_id)
);

-- Retention policy: Delete logs older than 90 days
CREATE INDEX idx_audit_logs_retention ON audit_logs(created_at)
WHERE created_at < NOW() - INTERVAL '90 days';
```

**Columns**:
- `id`: Primary key (UUID)
- `event_id`: Unique event identifier from CloudEvents (idempotency key)
- `timestamp`: Event timestamp from CloudEvents
- `user_id`: User who performed the action
- `event_type`: Type of event (task.created, task.updated, task.completed, task.deleted)
- `task_id`: Reference to task (nullable for user-level events)
- `payload`: Full event payload as JSONB for flexible querying
- `created_at`: Audit log entry creation time

**Access Control**:
- Administrators: SELECT on all rows
- Users: SELECT WHERE user_id = current_user_id

**Retention**:
- 90-day retention policy enforced via scheduled job
- Older logs archived or deleted based on compliance requirements

## Event Payload Structures

### Task Event

Published to `task-events` topic on task create/update/complete/delete operations.

```json
{
  "specversion": "1.0",
  "type": "com.todo.task.created | com.todo.task.updated | com.todo.task.completed | com.todo.task.deleted",
  "source": "backend-api",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "time": "2026-02-09T10:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440001",
    "user_id": "550e8400-e29b-41d4-a716-446655440002",
    "sequence": 123,
    "idempotency_key": "550e8400-e29b-41d4-a716-446655440000",
    "payload": {
      "title": "Weekly team meeting",
      "description": "Discuss project progress",
      "status": "pending",
      "priority": "high",
      "tags": ["work", "meeting"],
      "due_date": "2026-02-10T10:00:00Z",
      "recurring_pattern": "weekly",
      "recurring_interval": 1,
      "recurring_end_condition": "never",
      "changed_fields": ["status", "due_date"]
    }
  }
}
```

**Fields**:
- `specversion`: CloudEvents version (always "1.0")
- `type`: Event type following reverse-DNS naming
- `source`: Service that published the event
- `id`: Unique event identifier (UUID v4) - serves as idempotency key
- `time`: Event timestamp in ISO 8601 format with timezone
- `datacontenttype`: Content type of data field
- `data.task_id`: Task identifier
- `data.user_id`: User who performed the action
- `data.sequence`: Monotonically increasing sequence number per task
- `data.idempotency_key`: Duplicate of event ID for consumer convenience
- `data.payload`: Task-specific data (varies by event type)
- `data.payload.changed_fields`: Array of field names that changed (for updated events)

**Event Types**:
- `com.todo.task.created`: New task created
- `com.todo.task.updated`: Existing task updated
- `com.todo.task.completed`: Task marked as completed
- `com.todo.task.deleted`: Task deleted

### Reminder Event

Published to `reminders` topic when task due date is set or updated.

```json
{
  "specversion": "1.0",
  "type": "com.todo.reminder.schedule | com.todo.reminder.cancel",
  "source": "backend-api",
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "time": "2026-02-09T10:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440001",
    "user_id": "550e8400-e29b-41d4-a716-446655440002",
    "due_date": "2026-02-10T10:00:00Z",
    "reminder_time": "2026-02-10T09:45:00Z",
    "notification_channels": ["email", "push"],
    "user_email": "user@example.com",
    "device_tokens": ["fcm_token_1", "fcm_token_2"]
  }
}
```

**Fields**:
- `data.task_id`: Task identifier
- `data.user_id`: User to notify
- `data.due_date`: Task due date
- `data.reminder_time`: When to send reminder (calculated from due_date and user preferences)
- `data.notification_channels`: Array of channels (email, push)
- `data.user_email`: User's email address (for email notifications)
- `data.device_tokens`: Array of FCM device tokens (for push notifications)

**Event Types**:
- `com.todo.reminder.schedule`: Schedule a new reminder
- `com.todo.reminder.cancel`: Cancel an existing reminder

### Task Update Event

Published to `task-updates` topic for real-time synchronization to WebSocket clients.

```json
{
  "specversion": "1.0",
  "type": "com.todo.task.sync",
  "source": "sync-service",
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "time": "2026-02-09T10:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440001",
    "user_id": "550e8400-e29b-41d4-a716-446655440002",
    "sequence": 124,
    "changed_fields": {
      "status": "completed",
      "updated_at": "2026-02-09T10:00:00Z"
    }
  }
}
```

**Fields**:
- `data.task_id`: Task identifier
- `data.user_id`: User who owns the task
- `data.sequence`: Event sequence number for ordering
- `data.changed_fields`: Object with field names as keys and new values

## Dapr State Store Keys

### Reminder State

Stores scheduled reminder metadata for cancellation and recovery.

**Key Pattern**: `reminder:{task_id}`

**Value Structure**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440002",
  "reminder_time": "2026-02-10T09:45:00Z",
  "job_id": "reminder-job-550e8400",
  "scheduled_at": "2026-02-09T10:00:00Z"
}
```

**TTL**: 30 days (automatic cleanup after reminder expires)

**Operations**:
- Save: When reminder scheduled via Dapr Jobs API
- Get: When checking if reminder exists
- Delete: When reminder cancelled (task completed/deleted)

### Consumer Offset State

Stores event processing offsets for each consumer service.

**Key Pattern**: `consumer_offset:{service}:{topic}`

**Value Structure**:
```json
{
  "service": "recurring-task-service",
  "topic": "task-events",
  "partition": 0,
  "offset": 12345,
  "updated_at": "2026-02-09T10:00:00Z"
}
```

**TTL**: None (persists indefinitely)

**Operations**:
- Save: After successfully processing each event
- Get: On service startup to resume from last offset

### Event Sequence State

Stores monotonically increasing sequence numbers per task.

**Key Pattern**: `sequence:{task_id}`

**Value Structure**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440001",
  "current_sequence": 125,
  "updated_at": "2026-02-09T10:00:00Z"
}
```

**TTL**: None (persists indefinitely)

**Operations**:
- Increment: When publishing task event (atomic increment)
- Get: When client detects gap and requests missing events

### Processed Event IDs

Stores event IDs that have been processed for idempotency checking.

**Key Pattern**: `processed:{service}:{event_id}`

**Value Structure**:
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "processed_at": "2026-02-09T10:00:00Z",
  "service": "recurring-task-service"
}
```

**TTL**: 7 days (events older than 7 days assumed not to be replayed)

**Operations**:
- Save: After successfully processing event
- Get: Before processing event to check if already processed

## Entity Relationships

```
┌─────────────┐
│   users     │
└──────┬──────┘
       │
       │ 1:N
       │
┌──────▼──────┐         ┌──────────────┐
│   tasks     │────────▶│ audit_logs   │
└──────┬──────┘   N:1   └──────────────┘
       │
       │ publishes
       │
┌──────▼──────────────────────────────┐
│         Event Topics                │
│  ┌────────────────────────────────┐ │
│  │ task-events                    │ │
│  │ - task.created                 │ │
│  │ - task.updated                 │ │
│  │ - task.completed               │ │
│  │ - task.deleted                 │ │
│  └────────────────────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │ reminders                      │ │
│  │ - reminder.schedule            │ │
│  │ - reminder.cancel              │ │
│  └────────────────────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │ task-updates                   │ │
│  │ - task.sync                    │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
       │
       │ consumes
       │
┌──────▼──────────────────────────────┐
│      Consumer Services              │
│  ┌────────────────────────────────┐ │
│  │ Recurring Task Service         │ │
│  │ Notification Service           │ │
│  │ Audit Service                  │ │
│  │ Real-Time Sync Service         │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
       │
       │ stores state
       │
┌──────▼──────────────────────────────┐
│      Dapr State Store               │
│  ┌────────────────────────────────┐ │
│  │ reminder:{task_id}             │ │
│  │ consumer_offset:{svc}:{topic}  │ │
│  │ sequence:{task_id}             │ │
│  │ processed:{svc}:{event_id}     │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## Data Flow

### Task Creation Flow

1. User creates task via API → `POST /api/tasks`
2. Backend saves task to `tasks` table
3. Backend publishes `task.created` event to `task-events` topic
4. Audit Service consumes event → saves to `audit_logs` table
5. If task has due date → Backend publishes `reminder.schedule` event to `reminders` topic
6. Notification Service consumes event → schedules reminder via Dapr Jobs API
7. Sync Service consumes event → broadcasts to WebSocket clients

### Task Completion Flow (Recurring)

1. User completes task via API → `PUT /api/tasks/{id}/complete`
2. Backend updates task status in `tasks` table
3. Backend publishes `task.completed` event to `task-events` topic
4. Recurring Task Service consumes event → checks if task is recurring
5. If recurring → Service creates next occurrence via API → `POST /api/tasks`
6. Backend publishes `task.created` event for next occurrence
7. Audit Service logs both completion and creation events
8. Sync Service broadcasts both events to WebSocket clients

### Reminder Delivery Flow

1. Dapr Jobs API triggers reminder at scheduled time
2. Notification Service receives callback with task_id
3. Service retrieves task and user details from database
4. Service sends email via SendGrid API
5. Service sends push notification via Firebase Cloud Messaging
6. Service logs delivery status to audit log
7. On failure → Service retries with exponential backoff (1s, 5s, 25s)
8. After 3 failures → Event moved to dead-letter queue

## Validation Rules

### Event Validation

**Required Fields** (all events):
- `specversion`: Must be "1.0"
- `type`: Must match pattern `com.todo.*`
- `source`: Must be valid service name
- `id`: Must be valid UUID v4
- `time`: Must be valid ISO 8601 timestamp
- `data.task_id`: Must be valid UUID v4
- `data.user_id`: Must be valid UUID v4

**Task Event Specific**:
- `data.sequence`: Must be positive integer
- `data.payload.status`: Must be one of [pending, completed]
- `data.payload.priority`: Must be one of [high, medium, low]
- `data.payload.recurring_pattern`: Must be one of [daily, weekly, monthly, custom]

**Reminder Event Specific**:
- `data.due_date`: Must be future timestamp
- `data.reminder_time`: Must be before due_date
- `data.notification_channels`: Must contain at least one of [email, push]

### State Validation

**Reminder State**:
- `reminder_time`: Must be future timestamp
- `job_id`: Must be valid Dapr job identifier

**Consumer Offset State**:
- `offset`: Must be non-negative integer
- `partition`: Must be non-negative integer

**Sequence State**:
- `current_sequence`: Must be positive integer
- Must increment monotonically (no gaps or decrements)

## Migration Strategy

### Database Migration

```sql
-- Migration: Add audit_logs table
-- Version: 008-kafka-dapr-001
-- Date: 2026-02-09

BEGIN;

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL UNIQUE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id UUID NOT NULL REFERENCES users(id),
    event_type VARCHAR(50) NOT NULL,
    task_id UUID REFERENCES tasks(id),
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_task_id ON audit_logs(task_id);
CREATE INDEX idx_audit_logs_retention ON audit_logs(created_at)
WHERE created_at < NOW() - INTERVAL '90 days';

COMMIT;
```

### Dapr State Store Migration

```sql
-- Migration: Add dapr_state table for Dapr State Store
-- Version: 008-kafka-dapr-002
-- Date: 2026-02-09

BEGIN;

-- Create dapr_state table (required by Dapr PostgreSQL state store)
CREATE TABLE IF NOT EXISTS dapr_state (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    isbinary BOOLEAN NOT NULL,
    insertdate TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updatedate TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    eTag TEXT
);

-- Create index for TTL cleanup
CREATE INDEX idx_dapr_state_updatedate ON dapr_state(updatedate);

COMMIT;
```

## Rollback Strategy

### Database Rollback

```sql
-- Rollback: Remove audit_logs table
-- Version: 008-kafka-dapr-001-rollback

BEGIN;

DROP INDEX IF EXISTS idx_audit_logs_retention;
DROP INDEX IF EXISTS idx_audit_logs_task_id;
DROP INDEX IF EXISTS idx_audit_logs_event_type;
DROP INDEX IF EXISTS idx_audit_logs_timestamp;
DROP INDEX IF EXISTS idx_audit_logs_user_id;
DROP TABLE IF EXISTS audit_logs;

COMMIT;
```

### Dapr State Store Rollback

```sql
-- Rollback: Remove dapr_state table
-- Version: 008-kafka-dapr-002-rollback

BEGIN;

DROP INDEX IF EXISTS idx_dapr_state_updatedate;
DROP TABLE IF EXISTS dapr_state;

COMMIT;
```

## Performance Considerations

### Database Indexes

- `audit_logs.user_id`: Speeds up user-specific audit log queries
- `audit_logs.timestamp`: Speeds up time-range queries
- `audit_logs.event_type`: Speeds up event type filtering
- `audit_logs.task_id`: Speeds up task-specific audit queries
- `audit_logs.created_at`: Supports retention policy cleanup

### State Store Optimization

- Use bulk operations for batch state saves
- Set appropriate TTLs to prevent unbounded growth
- Use consistent key naming for efficient queries
- Leverage JSONB indexing for complex queries

### Event Payload Size

- Keep event payloads under 1 MB (Kafka message size limit)
- Use references (task_id) instead of embedding full task objects
- Compress large payloads if necessary
- Consider event payload versioning for future extensions

## Security Considerations

### Data Encryption

- Events encrypted in transit (TLS for Redpanda, Dapr)
- State encrypted at rest (PostgreSQL encryption)
- Audit logs contain sensitive data (apply same encryption as tasks)

### Access Control

- Audit logs: Row-level security (users see only own logs)
- State store: Service-level isolation (each service has own namespace)
- Events: User ID included for filtering at consumer level

### PII Handling

- Minimize PII in event payloads (use references)
- Audit logs may contain PII (apply data retention policies)
- Notification events include email/device tokens (secure transmission)

## Monitoring & Observability

### Metrics to Track

- Event publishing rate (events/second)
- Event processing latency (time from publish to consume)
- Consumer lag (offset difference between producer and consumer)
- State store operation latency
- Audit log write rate
- Sequence number gaps detected

### Alerts to Configure

- Consumer lag exceeds threshold (> 1000 events)
- Event processing failures exceed threshold (> 1% error rate)
- State store operation failures
- Audit log write failures (critical - must be 100% reliable)
- Sequence number gaps detected (indicates out-of-order events)

## Summary

✅ Database schema extended with `audit_logs` table
✅ Event payload structures defined (Task, Reminder, Task Update)
✅ Dapr state store key patterns documented
✅ Entity relationships mapped
✅ Data flows documented for key scenarios
✅ Validation rules defined
✅ Migration and rollback strategies provided
✅ Performance and security considerations addressed

**Ready for**: Contract generation (event schemas, Dapr components)
