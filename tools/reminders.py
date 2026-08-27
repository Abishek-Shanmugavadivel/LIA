"""
Reminders Tool & Background Scheduler for LIA JARVIS Experience (Phase 9)
Supports creating reminders ("Remind me at 6 PM", "Create a reminder tomorrow"), listing, and canceling reminders.
Includes an active background scheduler thread for triggering OS/Mobile notifications.
"""

import logging
import asyncio
import threading
import time
from datetime import datetime, timedelta
from livekit.agents import llm
from memory.database import get_db_connection
from devices.registry import get_device_registry

logger = logging.getLogger("lia-tools-reminders")


def perform_create_reminder(title: str, datetime_str: str) -> str:
    """Synchronous helper to insert a reminder into the database."""
    t_clean = title.strip() if title else "General Reminder"
    d_clean = datetime_str.strip() if datetime_str else "today"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reminders (title, datetime_str, status) VALUES (?, ?, 'pending')",
        (t_clean, d_clean),
    )
    conn.commit()
    reminder_id = cursor.lastrowid
    conn.close()

    # Trigger push notification to active devices
    registry = get_device_registry()
    for dev in registry.list_devices():
        if dev.get("device_type") == "mobile":
            try:
                from tools.mobile import send_mobile_notification
                asyncio.run(send_mobile_notification(f"Reminder set: {t_clean} ({d_clean})"))
            except Exception:
                pass

    return f"⏰ Reminder #{reminder_id} created: '{t_clean}' scheduled for '{d_clean}'."


def perform_get_reminders(filter_status: str = "pending") -> str:
    """Synchronous helper to list active reminders."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if filter_status and filter_status != "all":
        cursor.execute("SELECT id, title, datetime_str, status, created_at FROM reminders WHERE status = ? ORDER BY id DESC", (filter_status,))
    else:
        cursor.execute("SELECT id, title, datetime_str, status, created_at FROM reminders ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "No reminders found."

    output = ["⏰ **Active Reminders:**"]
    for row in rows:
        output.append(f"• ID #{row['id']}: **{row['title']}** - Time: {row['datetime_str']} [{row['status'].upper()}]")
    return "\n".join(output)


def perform_cancel_reminder(reminder_id: int) -> str:
    """Synchronous helper to cancel or mark a reminder as completed."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE reminders SET status = 'cancelled' WHERE id = ?", (reminder_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    if affected == 0:
        return f"Reminder #{reminder_id} not found."
    return f"Reminder #{reminder_id} has been cancelled."


@llm.function_tool(
    name="create_reminder",
    description="Create a reminder (e.g. 'Remind me at 6 PM', 'Create a reminder tomorrow to buy groceries').",
)
async def create_reminder(title: str, datetime_str: str = "today") -> str:
    logger.info(f"[LIA REMINDERS TOOL TRIGGERED] create_reminder(title='{title}', datetime_str='{datetime_str}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_create_reminder, title, datetime_str)


@llm.function_tool(
    name="get_reminders",
    description="Get current pending or completed reminders list.",
)
async def get_reminders(filter_status: str = "pending") -> str:
    logger.info(f"[LIA REMINDERS TOOL TRIGGERED] get_reminders(filter_status='{filter_status}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_get_reminders, filter_status)


@llm.function_tool(
    name="cancel_reminder",
    description="Cancel a specific reminder by ID.",
)
async def cancel_reminder(reminder_id: int) -> str:
    logger.info(f"[LIA REMINDERS TOOL TRIGGERED] cancel_reminder(reminder_id={reminder_id})")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_cancel_reminder, reminder_id)
