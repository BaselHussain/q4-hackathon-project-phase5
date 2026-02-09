"""
Contract tests for event schemas.

Validates that generated events comply with the JSON schemas
defined in specs/008-kafka-dapr/contracts/events/.
"""
import json
import os
import pytest
from uuid import uuid4
from datetime import datetime, timezone

from events.schemas import (
    CloudEvent,
    TaskEventPayload,
    TaskEventType,
    ReminderEventType,
)


CONTRACTS_DIR = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..", "specs", "008-kafka-dapr", "contracts", "events"
)


class TestTaskEventContract:
    """Validate task events against CloudEvents spec and contract schema."""

    def test_specversion_is_1_0(self):
        """CloudEvents specversion must be '1.0'."""
        event = CloudEvent.create_task_event(
            event_type=TaskEventType.CREATED,
            task_id=uuid4(),
            user_id=uuid4(),
            sequence=1,
            payload=TaskEventPayload(title="Test", status="pending"),
        )
        assert event.specversion == "1.0"

    def test_type_follows_reverse_dns(self):
        """Event type must follow com.todo.task.* pattern."""
        for etype in TaskEventType:
            assert etype.value.startswith("com.todo.task.")

    def test_source_is_set(self):
        """Source must identify the publishing service."""
        event = CloudEvent.create_task_event(
            event_type=TaskEventType.CREATED,
            task_id=uuid4(),
            user_id=uuid4(),
            sequence=1,
            payload=TaskEventPayload(title="Test", status="pending"),
        )
        assert event.source == "backend-api"

    def test_id_is_valid_uuid(self):
        """Event ID must be a valid UUID string."""
        event = CloudEvent.create_task_event(
            event_type=TaskEventType.CREATED,
            task_id=uuid4(),
            user_id=uuid4(),
            sequence=1,
            payload=TaskEventPayload(title="Test", status="pending"),
        )
        # Should not raise
        from uuid import UUID
        UUID(event.id)

    def test_time_is_iso8601(self):
        """Event time must be ISO 8601 format."""
        event = CloudEvent.create_task_event(
            event_type=TaskEventType.CREATED,
            task_id=uuid4(),
            user_id=uuid4(),
            sequence=1,
            payload=TaskEventPayload(title="Test", status="pending"),
        )
        # Should not raise
        datetime.fromisoformat(event.time)

    def test_data_has_required_fields(self):
        """Data envelope must have task_id, user_id, sequence, idempotency_key, payload."""
        task_id = uuid4()
        user_id = uuid4()
        event = CloudEvent.create_task_event(
            event_type=TaskEventType.CREATED,
            task_id=task_id,
            user_id=user_id,
            sequence=1,
            payload=TaskEventPayload(title="Test", status="pending"),
        )
        data = event.data
        assert "task_id" in data
        assert "user_id" in data
        assert "sequence" in data
        assert "idempotency_key" in data
        assert "payload" in data

    def test_idempotency_key_equals_event_id(self):
        """Idempotency key must equal event ID for consumer convenience."""
        event = CloudEvent.create_task_event(
            event_type=TaskEventType.CREATED,
            task_id=uuid4(),
            user_id=uuid4(),
            sequence=1,
            payload=TaskEventPayload(title="Test", status="pending"),
        )
        assert event.data["idempotency_key"] == event.id

    def test_sequence_is_positive_integer(self):
        """Sequence number must be a positive integer."""
        event = CloudEvent.create_task_event(
            event_type=TaskEventType.CREATED,
            task_id=uuid4(),
            user_id=uuid4(),
            sequence=42,
            payload=TaskEventPayload(title="Test", status="pending"),
        )
        assert event.data["sequence"] == 42
        assert isinstance(event.data["sequence"], int)
        assert event.data["sequence"] > 0

    def test_all_task_event_types_valid(self):
        """All four task event types should produce valid events."""
        for etype in TaskEventType:
            event = CloudEvent.create_task_event(
                event_type=etype,
                task_id=uuid4(),
                user_id=uuid4(),
                sequence=1,
                payload=TaskEventPayload(title="Test", status="pending"),
            )
            assert event.type == etype.value

    def test_event_serializable_to_json(self):
        """Event must be serializable to JSON."""
        event = CloudEvent.create_task_event(
            event_type=TaskEventType.CREATED,
            task_id=uuid4(),
            user_id=uuid4(),
            sequence=1,
            payload=TaskEventPayload(
                title="Test",
                description="A test task",
                status="pending",
                priority="high",
                tags=["test"],
                due_date="2026-03-01T10:00:00Z",
                recurring_pattern="daily",
            ),
        )
        # Should not raise
        json_str = event.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["specversion"] == "1.0"


class TestReminderEventContract:
    """Validate reminder events against contract schema."""

    def test_reminder_schedule_type(self):
        """Schedule event type must be com.todo.reminder.schedule."""
        event = CloudEvent.create_reminder_event(
            event_type=ReminderEventType.SCHEDULE,
            task_id=uuid4(),
            user_id=uuid4(),
            due_date=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc),
            reminder_time=datetime(2026, 3, 1, 9, 45, tzinfo=timezone.utc),
        )
        assert event.type == "com.todo.reminder.schedule"

    def test_reminder_cancel_type(self):
        """Cancel event type must be com.todo.reminder.cancel."""
        event = CloudEvent.create_reminder_event(
            event_type=ReminderEventType.CANCEL,
            task_id=uuid4(),
            user_id=uuid4(),
            due_date=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc),
            reminder_time=datetime(2026, 3, 1, 9, 45, tzinfo=timezone.utc),
        )
        assert event.type == "com.todo.reminder.cancel"

    def test_reminder_data_has_required_fields(self):
        """Reminder data must have task_id, user_id, due_date, reminder_time, notification_channels."""
        event = CloudEvent.create_reminder_event(
            event_type=ReminderEventType.SCHEDULE,
            task_id=uuid4(),
            user_id=uuid4(),
            due_date=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc),
            reminder_time=datetime(2026, 3, 1, 9, 45, tzinfo=timezone.utc),
        )
        data = event.data
        assert "task_id" in data
        assert "user_id" in data
        assert "due_date" in data
        assert "reminder_time" in data
        assert "notification_channels" in data

    def test_default_notification_channels(self):
        """Default notification channels should be email and push."""
        event = CloudEvent.create_reminder_event(
            event_type=ReminderEventType.SCHEDULE,
            task_id=uuid4(),
            user_id=uuid4(),
            due_date=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc),
            reminder_time=datetime(2026, 3, 1, 9, 45, tzinfo=timezone.utc),
        )
        assert event.data["notification_channels"] == ["email", "push"]


class TestSyncEventContract:
    """Validate task update/sync events against contract schema."""

    def test_sync_event_type(self):
        """Sync event type must be com.todo.task.sync."""
        event = CloudEvent.create_sync_event(
            task_id=uuid4(),
            user_id=uuid4(),
            sequence=1,
            changed_fields={"status": "completed"},
        )
        assert event.type == "com.todo.task.sync"

    def test_sync_data_has_required_fields(self):
        """Sync data must have task_id, user_id, sequence, changed_fields."""
        event = CloudEvent.create_sync_event(
            task_id=uuid4(),
            user_id=uuid4(),
            sequence=5,
            changed_fields={"status": "completed"},
        )
        data = event.data
        assert "task_id" in data
        assert "user_id" in data
        assert "sequence" in data
        assert "changed_fields" in data

    def test_changed_fields_is_dict(self):
        """Changed fields must be a dictionary."""
        event = CloudEvent.create_sync_event(
            task_id=uuid4(),
            user_id=uuid4(),
            sequence=1,
            changed_fields={"title": "New title", "status": "completed"},
        )
        assert isinstance(event.data["changed_fields"], dict)
        assert event.data["changed_fields"]["title"] == "New title"
