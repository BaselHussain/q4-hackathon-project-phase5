"""
Email notification handler using SendGrid API.

Sends task reminder emails with exponential backoff retry strategy.
Falls back to mock mode if SendGrid API key is not configured.
"""
import asyncio
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# SendGrid configuration
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "noreply@taskapp.com")
SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"

# Retry configuration (exponential backoff)
RETRY_DELAYS = [1.0, 5.0, 25.0]  # seconds


async def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Send email notification using SendGrid API.

    Implements exponential backoff retry strategy:
    - Retry 1: 1 second delay
    - Retry 2: 5 seconds delay
    - Retry 3: 25 seconds delay

    If SENDGRID_API_KEY is not configured, operates in mock mode.

    Args:
        to_email: Recipient email address
        subject: Email subject line
        body: Email body content (plain text)

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # Mock mode if no API key configured
    if not SENDGRID_API_KEY:
        logger.warning("SENDGRID_API_KEY not configured - operating in mock mode")
        logger.info(f"[MOCK] Email sent to {to_email}: {subject}")
        return True

    # Validate inputs
    if not to_email or not subject:
        logger.error(f"Invalid email parameters: to_email={to_email}, subject={subject}")
        return False

    # SendGrid API payload
    payload = {
        "personalizations": [
            {
                "to": [{"email": to_email}],
                "subject": subject
            }
        ],
        "from": {"email": SENDGRID_FROM_EMAIL},
        "content": [
            {
                "type": "text/plain",
                "value": body
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }

    # Retry loop with exponential backoff
    for attempt, delay in enumerate(RETRY_DELAYS, start=1):
        try:
            logger.info(f"Sending email to {to_email} (attempt {attempt}/{len(RETRY_DELAYS)})")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    SENDGRID_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except httpx.HTTPStatusError as e:
            logger.error(f"SendGrid API error (attempt {attempt}): HTTP {e.response.status_code} - {e.response.text}")

            # Don't retry on client errors (4xx)
            if 400 <= e.response.status_code < 500:
                logger.error(f"Client error - not retrying: {e.response.status_code}")
                return False

            # Retry on server errors (5xx)
            if attempt < len(RETRY_DELAYS):
                logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"Failed to send email after {len(RETRY_DELAYS)} attempts")
                return False

        except Exception as e:
            logger.error(f"Error sending email (attempt {attempt}): {str(e)}", exc_info=True)

            if attempt < len(RETRY_DELAYS):
                logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"Failed to send email after {len(RETRY_DELAYS)} attempts")
                return False

    return False
