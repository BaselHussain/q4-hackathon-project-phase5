"""
CloudEvents-compliant event schemas for Dapr Pub/Sub.

Follows CloudEvents 1.0 specification: https://cloudevents.io/
All events use reverse-DNS naming for event types.
"""
import enum
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskEventType(str, enum.Enum):
    """Event types for task lifecycle events."""
    CREATED = "com.todo.task.created"
    UPDATED = "com.todo.task.updated"
    COMPLETED = "com.todo.task.completed"
    DELETED = "com.todo.task.deleted"


class ReminderEventType(str, enum.Enum):
    """Event types for reminder events."""
    SCHEDULE = "com.todo.reminder.schedule"
    CANCEL = "com.todo.reminder.cancel"


class SyncEventType(str, enum.Enum):
    """Event types for real-time sync events."""
    SYNC = "com.todo.task.sync"


class TaskEventPayload(BaseModel):
    """Payload for task lifecycle events."""
    title: str
    description: Optional[str] = None
    status: str
    priority: str = "medium"
    tags: Optional[list[str]] = None
    due_date: Optional[str] = None
    recurring_pattern: str = "none"
    recurring_interval: int = 1
    changed_fields: Optional[list[str]] = None


class TaskEventData(BaseModel):
    """Data envelope for task events published to task-events topic."""
    task_id: str
    user_id: str
    sequence: int
    idempotency_key: str
    payload: TaskEventPayload


class ReminderEventData(BaseModel):
    """Data envelope for reminder events published to reminders topic."""
    task_id: str
    user_id: str
    due_date: str
    reminder_time: str
    notification_channels: list[str] = Field(default_factory=lambda: ["email", "push"])
    user_email: Optional[str] = None
    device_tokens: Optional[list[str]] = None


class TaskUpdateEventData(BaseModel):
    """Data envelope for task update events published to task-updates topic."""
    task_id: str
    user_id: str
    sequence: int
    changed_fields: dict[str, Any]


class CloudEvent(BaseModel):
    """
    CloudEvents 1.0 compliant event envelope.

    Used as the standard format for all events published via Dapr Pub/Sub.
    """
    specversion: str = "1.0"
    type: str
    source: str = "backend-api"
    id: str = Field(default_factory=lambda: str(uuid4()))
    time: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    datacontenttype: str = "application/json"
    data: dict[str, Any]

    @classmethod
    def create_task_event(
        cls,
        event_type: TaskEventType,
        task_id: UUID,
        user_id: UUID,
        sequence: int,
        payload: TaskEventPayload,
    ) -> "CloudEvent":
        """Create a CloudEvent for a task lifecycle event."""
        event_id = str(uuid4())
        data = TaskEventData(
            task_id=str(task_id),
            user_id=str(user_id),
            sequence=sequence,
            idempotency_key=event_id,
            payload=payload,
        )
        return cls(
            type=event_type.value,
            id=event_id,
            data=data.model_dump(),
        )

    @classmethod
    def create_reminder_event(
        cls,
        event_type: ReminderEventType,
        task_id: UUID,
        user_id: UUID,
        due_date: datetime,
        reminder_time: datetime,
        notification_channels: list[str] | None = None,
        user_email: str | None = None,
        device_tokens: list[str] | None = None,
    ) -> "CloudEvent":
        """Create a CloudEvent for a reminder event."""
        data = ReminderEventData(
            task_id=str(task_id),
            user_id=str(user_id),
            due_date=due_date.isoformat(),
            reminder_time=reminder_time.isoformat(),
            notification_channels=notification_channels or ["email", "push"],
            user_email=user_email,
            device_tokens=device_tokens,
        )
        return cls(
            type=event_type.value,
            data=data.model_dump(),
        )

    @classmethod
    def create_sync_event(
        cls,
        task_id: UUID,
        user_id: UUID,
        sequence: int,
        changed_fields: dict[str, Any],
    ) -> "CloudEvent":
        """Create a CloudEvent for a real-time sync event."""
        data = TaskUpdateEventData(
            task_id=str(task_id),
            user_id=str(user_id),
            sequence=sequence,
            changed_fields=changed_fields,
        )
        return cls(
            type=SyncEventType.SYNC.value,
            data=data.model_dump(),
        )
