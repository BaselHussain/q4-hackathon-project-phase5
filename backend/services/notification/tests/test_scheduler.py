"""
Unit tests for notification scheduler module.

Tests Dapr Jobs API integration and reminder time calculations.
"""
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

# Import scheduler functions
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scheduler import cancel_reminder, schedule_reminder, send_reminder_notification


class TestReminderTimeCalculation:
    """Test suite for reminder time calculation logic."""

    def test_reminder_time_calculation(self):
        """Test reminder time is calculated as due_date - 15 minutes."""
        due_date = datetime(2026, 2, 10, 10, 0, 0)  # 10:00 AM
        expected_reminder_time = datetime(2026, 2, 10, 9, 45, 0)  # 9:45 AM

        # Calculate reminder time (15 minutes before due date)
        reminder_time = due_date - timedelta(minutes=15)

        assert reminder_time == expected_reminder_time
        assert reminder_time.isoformat() == "2026-02-10T09:45:00"

    def test_reminder_time_different_intervals(self):
        """Test reminder time calculation with different intervals."""
        due_date = datetime(2026, 2, 10, 14, 30, 0)

        # 15 minutes before
        reminder_15min = due_date - timedelta(minutes=15)
        assert reminder_15min == datetime(2026, 2, 10, 14, 15, 0)

        # 1 hour before
        reminder_1hr = due_date - timedelta(hours=1)
        assert reminder_1hr == datetime(2026, 2, 10, 13, 30, 0)

        # 1 day before
        reminder_1day = due_date - timedelta(days=1)
        assert reminder_1day == datetime(2026, 2, 9, 14, 30, 0)


class TestScheduleReminder:
    """Test suite for schedule_reminder function."""

    @pytest.mark.asyncio
    async def test_schedule_reminder_calls_dapr_jobs_api(self):
        """Test that schedule_reminder makes correct HTTP POST to Dapr Jobs API."""
        task_id = "test-task-123"
        reminder_time = "2026-02-10T09:45:00Z"
        task_data = {
            "task_id": task_id,
            "user_id": "user-456",
            "due_date": "2026-02-10T10:00:00Z",
            "user_email": "user@example.com",
            "device_tokens": ["token123"],
            "notification_channels": ["email", "push"]
        }

        # Mock httpx.AsyncClient
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            # Call schedule_reminder
            await schedule_reminder(task_id, reminder_time, task_data)

            # Verify POST call to Dapr Jobs API
            assert mock_client.post.call_count == 2  # One for job, one for state

            # Check first call (schedule job)
            first_call = mock_client.post.call_args_list[0]
            assert "v1.0-alpha1/jobs/reminder-test-task-123" in first_call[0][0]

            # Verify job payload
            job_payload = first_call[1]['json']
            assert job_payload['schedule'] == reminder_time
            assert job_payload['data'] == task_data
            assert job_payload['repeats'] == 0

    @pytest.mark.asyncio
    async def test_schedule_reminder_handles_http_errors(self):
        """Test that schedule_reminder handles HTTP errors from Dapr Jobs API."""
        task_id = "test-task-456"
        reminder_time = "2026-02-10T09:45:00Z"
        task_data = {"task_id": task_id, "user_id": "user-789"}

        # Mock HTTP error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError("Server error", request=MagicMock(), response=mock_response)
        )

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            # Call should raise exception
            with pytest.raises(httpx.HTTPStatusError):
                await schedule_reminder(task_id, reminder_time, task_data)


class TestCancelReminder:
    """Test suite for cancel_reminder function."""

    @pytest.mark.asyncio
    async def test_cancel_reminder_calls_dapr_jobs_api(self):
        """Test that cancel_reminder makes correct HTTP DELETE to Dapr Jobs API."""
        task_id = "test-task-789"

        # Mock successful deletion
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.delete = AsyncMock(return_value=mock_response)
            mock_client.post = AsyncMock(return_value=mock_response)  # For state save
            mock_client_class.return_value = mock_client

            # Call cancel_reminder
            await cancel_reminder(task_id)

            # Verify DELETE call to Dapr Jobs API
            assert mock_client.delete.call_count == 1
            delete_call = mock_client.delete.call_args
            assert "v1.0-alpha1/jobs/reminder-test-task-789" in delete_call[0][0]

    @pytest.mark.asyncio
    async def test_cancel_reminder_handles_not_found(self):
        """Test that cancel_reminder handles 404 (job not found) gracefully."""
        task_id = "test-task-999"

        # Mock 404 response (job already triggered or doesn't exist)
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.delete = AsyncMock(return_value=mock_response)
            mock_client.post = AsyncMock(return_value=mock_response)  # For state save
            mock_client_class.return_value = mock_client

            # Should not raise exception for 404
            await cancel_reminder(task_id)

            # Verify DELETE was called
            assert mock_client.delete.call_count == 1


class TestSendReminderNotification:
    """Test suite for send_reminder_notification function."""

    @pytest.mark.asyncio
    async def test_send_reminder_notification_calls_email_and_push(self):
        """Test that send_reminder_notification calls both email and push notifiers."""
        task_id = "test-task-111"
        job_data = {
            "task_id": task_id,
            "user_id": "user-222",
            "due_date": "2026-02-10T10:00:00Z",
            "user_email": "user@example.com",
            "device_tokens": ["token456"],
            "notification_channels": ["email", "push"]
        }

        # Mock notifiers
        with patch('scheduler.send_email', new_callable=AsyncMock) as mock_email, \
             patch('scheduler.send_push', new_callable=AsyncMock) as mock_push, \
             patch('scheduler.save_reminder_state', new_callable=AsyncMock) as mock_save:

            mock_email.return_value = True
            mock_push.return_value = True

            # Call send_reminder_notification
            await send_reminder_notification(task_id, job_data)

            # Verify email was called
            assert mock_email.call_count == 1
            email_call = mock_email.call_args
            assert email_call[0][0] == "user@example.com"
            assert "Task Reminder" in email_call[0][1]

            # Verify push was called
            assert mock_push.call_count == 1
            push_call = mock_push.call_args
            assert push_call[0][0] == "token456"
            assert "Task Reminder" in push_call[0][1]

            # Verify state was saved
            assert mock_save.call_count == 1

    @pytest.mark.asyncio
    async def test_send_reminder_notification_email_only(self):
        """Test notification when only email channel is configured."""
        task_id = "test-task-333"
        job_data = {
            "task_id": task_id,
            "user_id": "user-444",
            "due_date": "2026-02-10T10:00:00Z",
            "user_email": "user@example.com",
            "notification_channels": ["email"]
        }

        with patch('scheduler.send_email', new_callable=AsyncMock) as mock_email, \
             patch('scheduler.send_push', new_callable=AsyncMock) as mock_push, \
             patch('scheduler.save_reminder_state', new_callable=AsyncMock):

            mock_email.return_value = True

            await send_reminder_notification(task_id, job_data)

            # Email should be called
            assert mock_email.call_count == 1

            # Push should NOT be called
            assert mock_push.call_count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
