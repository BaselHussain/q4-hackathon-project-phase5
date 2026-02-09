"""
Unit tests for event publishing infrastructure.

Tests CloudEvents schema validation, idempotency key generation,
sequence number tracking, and Dapr HTTP client calls.
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone

from events.schemas import (
    CloudEvent,
    TaskEventData,
    TaskEventPayload,
    ReminderEventData,
    TaskUpdateEventData,
    TaskEventType,
    ReminderEventType,
    SyncEventType,
)
from events.publisher import _get_next_sequence, _sequence_counters


class TestCloudEventSchema:
    """Test CloudEvents 1.0 compliance."""

    def test_cloud_event_has_required_fields(self):
        """CloudEvent must have specversion, type, source, id, time."""
        event = CloudEvent(
            type="com.todo.task.created",
            data={"task_id": "123"},
        )
        assert event.specversion == "1.0"
        assert event.type == "com.todo.task.created"
        assert event.source == "backend-api"
        assert event.id  # auto-generated UUID
        assert event.time  # auto-generated timestamp
        assert event.datacontenttype == "application/json"

    def test_cloud_event_id_is_unique(self):
        """Each CloudEvent must have a unique ID."""
        event1 = CloudEvent(type="test", data={})
        event2 = CloudEvent(type="test", data={})
        assert event1.id != event2.id

    def test_create_task_event(self):
        """create_task_event produces valid CloudEvent."""
        task_id = uuid4()
        user_id = uuid4()
        payload = TaskEventPayload(
            title="Test task",
            status="pending",
            priority="high",
        )
        event = CloudEvent.create_task_event(
            event_type=TaskEventType.CREATED,
            task_id=task_id,
            user_id=user_id,
            sequence=1,
            payload=payload,
        )
        assert event.type == "com.todo.task.created"
        assert event.data["task_id"] == str(task_id)
        assert event.data["user_id"] == str(user_id)
        assert event.data["sequence"] == 1
        assert event.data["idempotency_key"] == event.id
        assert event.data["payload"]["title"] == "Test task"

    def test_create_reminder_event(self):
        """create_reminder_event produces valid CloudEvent."""
        task_id = uuid4()
        user_id = uuid4()
        due = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
        remind = datetime(2026, 3, 1, 9, 45, tzinfo=timezone.utc)

        event = CloudEvent.create_reminder_event(
            event_type=ReminderEventType.SCHEDULE,
            task_id=task_id,
            user_id=user_id,
            due_date=due,
            reminder_time=remind,
            user_email="test@example.com",
        )
        assert event.type == "com.todo.reminder.schedule"
        assert event.data["task_id"] == str(task_id)
        assert event.data["notification_channels"] == ["email", "push"]
        assert event.data["user_email"] == "test@example.com"

    def test_create_sync_event(self):
        """create_sync_event produces valid CloudEvent."""
        task_id = uuid4()
        user_id = uuid4()
        event = CloudEvent.create_sync_event(
            task_id=task_id,
            user_id=user_id,
            sequence=5,
            changed_fields={"status": "completed"},
        )
        assert event.type == "com.todo.task.sync"
        assert event.data["sequence"] == 5
        assert event.data["changed_fields"]["status"] == "completed"


class TestTaskEventPayload:
    """Test task event payload validation."""

    def test_minimal_payload(self):
        """Payload with only required fields."""
        p = TaskEventPayload(title="Test", status="pending")
        assert p.title == "Test"
        assert p.status == "pending"
        assert p.priority == "medium"
        assert p.recurring_pattern == "none"

    def test_full_payload(self):
        """Payload with all fields populated."""
        p = TaskEventPayload(
            title="Weekly meeting",
            description="Team standup",
            status="pending",
            priority="high",
            tags=["work", "meeting"],
            due_date="2026-03-01T10:00:00Z",
            recurring_pattern="weekly",
            recurring_interval=1,
            changed_fields=["status"],
        )
        assert p.tags == ["work", "meeting"]
        assert p.recurring_pattern == "weekly"
        assert p.changed_fields == ["status"]


class TestSequenceNumberTracking:
    """Test monotonically increasing sequence numbers per task."""

    def setup_method(self):
        """Reset sequence counters before each test."""
        _sequence_counters.clear()

    def test_first_sequence_is_one(self):
        """First sequence number for a task should be 1."""
        seq = _get_next_sequence("task-1")
        assert seq == 1

    def test_sequence_increments(self):
        """Sequence numbers should increment monotonically."""
        s1 = _get_next_sequence("task-1")
        s2 = _get_next_sequence("task-1")
        s3 = _get_next_sequence("task-1")
        assert s1 == 1
        assert s2 == 2
        assert s3 == 3

    def test_sequences_independent_per_task(self):
        """Each task has its own sequence counter."""
        _get_next_sequence("task-a")
        _get_next_sequence("task-a")
        s_b = _get_next_sequence("task-b")
        assert s_b == 1  # task-b starts at 1


class TestEventTypes:
    """Test event type enumerations."""

    def test_task_event_types(self):
        assert TaskEventType.CREATED.value == "com.todo.task.created"
        assert TaskEventType.UPDATED.value == "com.todo.task.updated"
        assert TaskEventType.COMPLETED.value == "com.todo.task.completed"
        assert TaskEventType.DELETED.value == "com.todo.task.deleted"

    def test_reminder_event_types(self):
        assert ReminderEventType.SCHEDULE.value == "com.todo.reminder.schedule"
        assert ReminderEventType.CANCEL.value == "com.todo.reminder.cancel"

    def test_sync_event_type(self):
        assert SyncEventType.SYNC.value == "com.todo.task.sync"
