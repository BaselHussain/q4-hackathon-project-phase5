"""
Integration tests for event-driven architecture flows.

Tests end-to-end event flows with mocked Dapr sidecar.
"""
import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from events.publisher import publish_task_event, publish_reminder_event, publish_sync_event
from events.schemas import TaskEventType, TaskEventPayload, ReminderEventType


@pytest.mark.integration
class TestTaskEventFlow:
    """Test task lifecycle event publishing."""

    @pytest.mark.asyncio
    @patch("events.publisher.httpx.AsyncClient")
    async def test_task_created_event_published(self, mock_client_cls):
        """Creating a task should publish a task.created event."""
        mock_response = AsyncMock()
        mock_response.raise_for_status = lambda: None
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        payload = TaskEventPayload(title="Test", status="pending")
        result = await publish_task_event(
            event_type=TaskEventType.CREATED,
            task_id=uuid4(),
            user_id=uuid4(),
            payload=payload,
        )

        assert result is True
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "task-events" in call_args.args[0]


@pytest.mark.integration
class TestReminderEventFlow:
    """Test reminder scheduling event flow."""

    @pytest.mark.asyncio
    @patch("events.publisher.httpx.AsyncClient")
    async def test_reminder_schedule_published(self, mock_client_cls):
        """Setting a due date should publish a reminder.schedule event."""
        mock_response = AsyncMock()
        mock_response.raise_for_status = lambda: None
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        due = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
        remind = datetime(2026, 3, 1, 9, 45, tzinfo=timezone.utc)

        result = await publish_reminder_event(
            event_type=ReminderEventType.SCHEDULE,
            task_id=uuid4(),
            user_id=uuid4(),
            due_date=due,
            reminder_time=remind,
        )

        assert result is True
        call_args = mock_client.post.call_args
        assert "reminders" in call_args.args[0]


@pytest.mark.integration
class TestSyncEventFlow:
    """Test real-time sync event flow."""

    @pytest.mark.asyncio
    @patch("events.publisher.httpx.AsyncClient")
    async def test_sync_event_published(self, mock_client_cls):
        """Updating a task should publish a sync event."""
        mock_response = AsyncMock()
        mock_response.raise_for_status = lambda: None
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        result = await publish_sync_event(
            task_id=uuid4(),
            user_id=uuid4(),
            changed_fields={"status": "completed"},
        )

        assert result is True
        call_args = mock_client.post.call_args
        assert "task-updates" in call_args.args[0]
