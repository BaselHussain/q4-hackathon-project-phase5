"""
Unit tests for task creation logic.

Tests recurrence pattern calculation and idempotency guarantees.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from task_creator import calculate_next_due_date, create_next_task_occurrence


class TestCalculateNextDueDate:
    """Tests for calculate_next_due_date function."""

    def test_daily_recurrence(self):
        """Test daily recurrence adds 1 day."""
        current = "2024-01-15T10:00:00+00:00"
        result = calculate_next_due_date(current, "daily")

        assert result is not None
        expected = datetime(2024, 1, 16, 10, 0, 0, tzinfo=timezone.utc)
        assert result == expected

    def test_weekly_recurrence(self):
        """Test weekly recurrence adds 7 days."""
        current = "2024-01-15T10:00:00+00:00"
        result = calculate_next_due_date(current, "weekly")

        assert result is not None
        expected = datetime(2024, 1, 22, 10, 0, 0, tzinfo=timezone.utc)
        assert result == expected

    def test_monthly_recurrence(self):
        """Test monthly recurrence adds 1 month."""
        current = "2024-01-15T10:00:00+00:00"
        result = calculate_next_due_date(current, "monthly")

        assert result is not None
        expected = datetime(2024, 2, 15, 10, 0, 0, tzinfo=timezone.utc)
        assert result == expected

    def test_monthly_recurrence_end_of_month(self):
        """Test monthly recurrence handles end-of-month correctly."""
        # January 31st -> February 29th (2024 is leap year)
        current = "2024-01-31T10:00:00+00:00"
        result = calculate_next_due_date(current, "monthly")

        assert result is not None
        # relativedelta handles this gracefully
        expected = datetime(2024, 2, 29, 10, 0, 0, tzinfo=timezone.utc)
        assert result == expected

    def test_yearly_recurrence(self):
        """Test yearly recurrence adds 1 year."""
        current = "2024-01-15T10:00:00+00:00"
        result = calculate_next_due_date(current, "yearly")

        assert result is not None
        expected = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        assert result == expected

    def test_yearly_recurrence_leap_day(self):
        """Test yearly recurrence handles leap day correctly."""
        # Feb 29, 2024 -> Feb 28, 2025 (not a leap year)
        current = "2024-02-29T10:00:00+00:00"
        result = calculate_next_due_date(current, "yearly")

        assert result is not None
        expected = datetime(2025, 2, 28, 10, 0, 0, tzinfo=timezone.utc)
        assert result == expected

    def test_no_recurrence_returns_none(self):
        """Test 'none' recurrence pattern returns None."""
        current = "2024-01-15T10:00:00+00:00"
        result = calculate_next_due_date(current, "none")

        assert result is None

    def test_invalid_pattern_returns_none(self):
        """Test invalid recurrence pattern returns None."""
        current = "2024-01-15T10:00:00+00:00"
        result = calculate_next_due_date(current, "invalid")

        assert result is None

    def test_none_due_date_returns_none(self):
        """Test None due date returns None."""
        result = calculate_next_due_date(None, "daily")
        assert result is None

    def test_invalid_date_format_returns_none(self):
        """Test invalid date format returns None."""
        result = calculate_next_due_date("invalid-date", "daily")
        assert result is None

    def test_case_insensitive_patterns(self):
        """Test recurrence patterns are case-insensitive."""
        current = "2024-01-15T10:00:00+00:00"

        daily = calculate_next_due_date(current, "DAILY")
        assert daily is not None

        weekly = calculate_next_due_date(current, "Weekly")
        assert weekly is not None

        monthly = calculate_next_due_date(current, "MoNtHLy")
        assert monthly is not None


class TestCreateNextTaskOccurrence:
    """Tests for create_next_task_occurrence function."""

    @pytest.mark.asyncio
    async def test_successful_task_creation(self):
        """Test successful task creation via API."""
        event_data = {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "payload": {
                "title": "Daily standup",
                "description": "Team sync meeting",
                "priority": "high",
                "tags": ["work", "meeting"],
                "recurring_pattern": "daily",
                "due_date": "2024-01-15T10:00:00+00:00",
            },
        }

        mock_response = AsyncMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "new-task-id",
            "title": "Daily standup",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_instance.post.return_value = mock_response
            mock_client.return_value = mock_instance

            result = await create_next_task_occurrence(event_data)

        assert result is True

    @pytest.mark.asyncio
    async def test_missing_user_id_fails(self):
        """Test missing user_id returns False."""
        event_data = {
            "payload": {
                "title": "Task",
                "recurring_pattern": "daily",
                "due_date": "2024-01-15T10:00:00+00:00",
            },
        }

        result = await create_next_task_occurrence(event_data)
        assert result is False

    @pytest.mark.asyncio
    async def test_missing_title_fails(self):
        """Test missing title returns False."""
        event_data = {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "payload": {
                "recurring_pattern": "daily",
                "due_date": "2024-01-15T10:00:00+00:00",
            },
        }

        result = await create_next_task_occurrence(event_data)
        assert result is False

    @pytest.mark.asyncio
    async def test_client_error_no_retry(self):
        """Test client errors (4xx) are not retried."""
        event_data = {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "payload": {
                "title": "Invalid task",
                "recurring_pattern": "daily",
                "due_date": "2024-01-15T10:00:00+00:00",
            },
        }

        mock_response = AsyncMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_instance.post.return_value = mock_response
            mock_client.return_value = mock_instance

            result = await create_next_task_occurrence(event_data)

        assert result is False
        # Should only attempt once (no retries for client errors)
        assert mock_instance.post.call_count == 1

    @pytest.mark.asyncio
    async def test_server_error_retries_with_backoff(self):
        """Test server errors (5xx) are retried with exponential backoff."""
        event_data = {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "payload": {
                "title": "Daily task",
                "recurring_pattern": "daily",
                "due_date": "2024-01-15T10:00:00+00:00",
            },
        }

        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("httpx.AsyncClient") as mock_client, \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_instance.post.return_value = mock_response
            mock_instance.aclose.return_value = None
            mock_client.return_value = mock_instance

            result = await create_next_task_occurrence(event_data)

        assert result is False
        # Should retry 3 times
        assert mock_instance.post.call_count == 3
        # Should sleep between retries (2 times: after 1st and 2nd attempt)
        assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    async def test_connection_error_retries(self):
        """Test connection errors are retried."""
        event_data = {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "payload": {
                "title": "Daily task",
                "recurring_pattern": "daily",
                "due_date": "2024-01-15T10:00:00+00:00",
            },
        }

        import httpx

        with patch("httpx.AsyncClient") as mock_client, \
             patch("asyncio.sleep", new_callable=AsyncMock):

            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_instance.post.side_effect = httpx.ConnectError("Connection refused")
            mock_instance.aclose.return_value = None
            mock_client.return_value = mock_instance

            result = await create_next_task_occurrence(event_data)

        assert result is False
        # Should retry 3 times
        assert mock_instance.post.call_count == 3


class TestIdempotency:
    """Tests for idempotency guarantees."""

    @pytest.mark.asyncio
    async def test_idempotency_prevents_duplicates(self):
        """Test same event ID is only processed once."""
        # Import consumer module to test idempotency
        from consumer import handle_task_event, _processed_events

        # Clear processed events set
        _processed_events.clear()

        event = {
            "id": "unique-event-123",
            "type": "com.todo.task.completed",
            "data": {
                "task_id": "task-456",
                "user_id": "user-789",
                "payload": {
                    "title": "Test task",
                    "recurring_pattern": "daily",
                    "due_date": "2024-01-15T10:00:00+00:00",
                },
            },
        }

        # Mock task creation to succeed
        with patch("consumer.create_next_task_occurrence", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = True

            # First call should process the event
            result1 = await handle_task_event(event)
            assert result1 is True
            assert mock_create.call_count == 1

            # Second call with same event ID should skip processing
            result2 = await handle_task_event(event)
            assert result2 is True
            # Should still be 1 (not called again)
            assert mock_create.call_count == 1

        # Clean up
        _processed_events.clear()

    @pytest.mark.asyncio
    async def test_non_recurring_task_skipped(self):
        """Test non-recurring tasks are skipped gracefully."""
        from consumer import handle_task_event, _processed_events

        _processed_events.clear()

        event = {
            "id": "non-recurring-event",
            "type": "com.todo.task.completed",
            "data": {
                "task_id": "task-456",
                "user_id": "user-789",
                "payload": {
                    "title": "One-time task",
                    "recurring_pattern": "none",
                    "due_date": "2024-01-15T10:00:00+00:00",
                },
            },
        }

        with patch("consumer.create_next_task_occurrence", new_callable=AsyncMock) as mock_create:
            result = await handle_task_event(event)

            assert result is True
            # Should not call create_next_task_occurrence for non-recurring
            assert mock_create.call_count == 0

        _processed_events.clear()
