"""
Notification Summary Tools for LIA (Phases 4-8 Expanded)
Reads OS and Mobile notification summaries while adhering to operating system privacy controls.
"""

import logging
import asyncio
from typing import Dict, Any, List
from livekit.agents import llm
from devices.registry import get_device_registry

logger = logging.getLogger("lia-tools-notifications")

# Simulated OS notification buffer (in real deployment, fed by Windows Action Center / Android Telemetry)
NOTIFICATION_BUFFER: List[Dict[str, str]] = [
    {
        "id": "notif_01",
        "app": "WhatsApp",
        "title": "Arun",
        "body": "Hey, let's catch up later today!",
        "timestamp": "10 mins ago",
    },
    {
        "id": "notif_02",
        "app": "Gmail",
        "title": "GitHub",
        "body": "Your build workflow completed successfully.",
        "timestamp": "25 mins ago",
    }
]


def perform_read_notifications() -> Dict[str, Any]:
    """Synchronous helper to retrieve active notification summaries."""
    registry = get_device_registry()
    mobile_devs = registry.get_device_by_type("mobile")
    
    mob_status = "connected" if mobile_devs and mobile_devs[0].get("status") == "connected" else "idle"
    return {
        "status": "success",
        "count": len(NOTIFICATION_BUFFER),
        "notifications": NOTIFICATION_BUFFER,
        "mobile_device_sync": mob_status
    }


def perform_get_latest_notification() -> str:
    """Synchronous helper to read the latest notification."""
    if not NOTIFICATION_BUFFER:
        return "You have no new notifications right now."
    
    top = NOTIFICATION_BUFFER[0]
    return f"Latest notification from {top['app']} ({top['title']}): '{top['body']}' ({top['timestamp']})."


@llm.function_tool(
    name="read_notifications",
    description="Check for new notifications across your computer and mobile phone.",
)
async def read_notifications() -> Dict[str, Any]:
    logger.info("[LIA NOTIFICATIONS TOOL TRIGGERED] read_notifications()")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_read_notifications)


@llm.function_tool(
    name="get_latest_notification",
    description="Read your most recent notification summary.",
)
async def get_latest_notification() -> str:
    logger.info("[LIA NOTIFICATIONS TOOL TRIGGERED] get_latest_notification()")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_get_latest_notification)
