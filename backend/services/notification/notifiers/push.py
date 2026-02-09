"""
Push notification handler using Firebase Cloud Messaging (FCM).

Sends task reminder push notifications with exponential backoff retry strategy.
Falls back to mock mode if FCM server key is not configured.
"""
import asyncio
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Firebase Cloud Messaging configuration
FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY")
FCM_API_URL = "https://fcm.googleapis.com/fcm/send"

# Retry configuration (exponential backoff)
RETRY_DELAYS = [1.0, 5.0, 25.0]  # seconds


async def send_push(device_token: str, title: str, body: str) -> bool:
    """
    Send push notification using Firebase Cloud Messaging.

    Implements exponential backoff retry strategy:
    - Retry 1: 1 second delay
    - Retry 2: 5 seconds delay
    - Retry 3: 25 seconds delay

    If FCM_SERVER_KEY is not configured, operates in mock mode.

    Args:
        device_token: FCM device registration token
        title: Notification title
        body: Notification body text

    Returns:
        bool: True if notification sent successfully, False otherwise
    """
    # Mock mode if no server key configured
    if not FCM_SERVER_KEY:
        logger.warning("FCM_SERVER_KEY not configured - operating in mock mode")
        logger.info(f"[MOCK] Push notification sent to device {device_token[:10]}...: {title}")
        return True

    # Validate inputs
    if not device_token or not title:
        logger.error(f"Invalid push parameters: device_token={device_token[:10] if device_token else None}, title={title}")
        return False

    # FCM API payload
    payload = {
        "to": device_token,
        "notification": {
            "title": title,
            "body": body,
            "sound": "default"
        },
        "priority": "high"
    }

    headers = {
        "Authorization": f"key={FCM_SERVER_KEY}",
        "Content-Type": "application/json"
    }

    # Retry loop with exponential backoff
    for attempt, delay in enumerate(RETRY_DELAYS, start=1):
        try:
            logger.info(f"Sending push notification to device {device_token[:10]}... (attempt {attempt}/{len(RETRY_DELAYS)})")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    FCM_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()

                # Check FCM-specific error codes in response body
                response_data = response.json()
                if response_data.get("failure", 0) > 0:
                    results = response_data.get("results", [])
                    if results and "error" in results[0]:
                        error = results[0]["error"]
                        logger.error(f"FCM error: {error}")

                        # Don't retry on invalid registration tokens
                        if error in ["InvalidRegistration", "NotRegistered"]:
                            logger.error(f"Invalid device token - not retrying")
                            return False

                        # Retry on server errors
                        if attempt < len(RETRY_DELAYS):
                            logger.info(f"Retrying in {delay} seconds...")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            return False

            logger.info(f"Push notification sent successfully to device {device_token[:10]}...")
            return True

        except httpx.HTTPStatusError as e:
            logger.error(f"FCM API error (attempt {attempt}): HTTP {e.response.status_code} - {e.response.text}")

            # Don't retry on client errors (4xx)
            if 400 <= e.response.status_code < 500:
                logger.error(f"Client error - not retrying: {e.response.status_code}")
                return False

            # Retry on server errors (5xx)
            if attempt < len(RETRY_DELAYS):
                logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"Failed to send push notification after {len(RETRY_DELAYS)} attempts")
                return False

        except Exception as e:
            logger.error(f"Error sending push notification (attempt {attempt}): {str(e)}", exc_info=True)

            if attempt < len(RETRY_DELAYS):
                logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"Failed to send push notification after {len(RETRY_DELAYS)} attempts")
                return False

    return False
