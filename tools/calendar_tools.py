"""
Calendar & Schedule Management Tool for LIA JARVIS Experience (Phase 9)
Supports checking schedule ("What is my schedule today?"), adding events ("Add meeting tomorrow at 3 PM"), and deleting events.
"""

import logging
import asyncio
from datetime import datetime, timedelta
# pyrefly: ignore [missing-import]
from livekit.agents import llm
from memory.database import get_db_connection

logger = logging.getLogger("lia-tools-calendar")


def perform_get_calendar_events(date_str: str = "today") -> str:
    """Synchronous helper to retrieve calendar events."""
    d_clean = date_str.strip().lower() if date_str else "today"
    
    if d_clean in ["today", "now"]:
        search_date = datetime.now().strftime("%Y-%m-%d")
    elif d_clean == "tomorrow":
        search_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        search_date = d_clean

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, date_str, time_str, duration_mins, location FROM calendar_events WHERE date_str LIKE ? OR date_str = ? ORDER BY time_str ASC",
        (f"%{search_date}%", d_clean),
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return f"📅 No meetings or events scheduled for {date_str} ({search_date})."

    events_list = [f"📅 **Schedule for {date_str.title()} ({search_date}):**"]
    for row in rows:
        events_list.append(
            f"• Event #{row['id']}: **{row['title']}** at {row['time_str']} ({row['duration_mins']} mins) - Location: {row['location']}"
        )
    return "\n".join(events_list)


def perform_add_calendar_event(
    title: str, date_str: str = "tomorrow", time_str: str = "10:00 AM", duration_mins: int = 60, location: str = "Online"
) -> str:
    """Synchronous helper to insert a new calendar event."""
    t_clean = title.strip() if title else "Meeting"
    d_clean = date_str.strip() if date_str else "tomorrow"
    tm_clean = time_str.strip() if time_str else "10:00 AM"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO calendar_events (title, date_str, time_str, duration_mins, location) VALUES (?, ?, ?, ?, ?)",
        (t_clean, d_clean, tm_clean, duration_mins, location),
    )
    conn.commit()
    event_id = cursor.lastrowid
    conn.close()

    return f"📅 Meeting scheduled! Event #{event_id}: '{t_clean}' on {d_clean} at {tm_clean} ({duration_mins} mins)."


def perform_delete_calendar_event(event_id: int) -> str:
    """Synchronous helper to delete a calendar event."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM calendar_events WHERE id = ?", (event_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    if affected == 0:
        return f"Calendar event #{event_id} not found."
    return f"Calendar event #{event_id} has been removed."


@llm.function_tool(
    name="get_calendar_events",
    description="Get schedule or calendar meetings for today, tomorrow, or a specific date (e.g. 'What is my schedule today?').",
)
async def get_calendar_events(date_str: str = "today") -> str:
    logger.info(f"[LIA CALENDAR TOOL TRIGGERED] get_calendar_events(date_str='{date_str}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_get_calendar_events, date_str)


@llm.function_tool(
    name="add_calendar_event",
    description="Add a meeting or calendar event (e.g. 'Add meeting tomorrow at 3 PM with Team').",
)
async def add_calendar_event(
    title: str, date_str: str = "tomorrow", time_str: str = "10:00 AM", duration_mins: int = 60, location: str = "Online"
) -> str:
    logger.info(
        f"[LIA CALENDAR TOOL TRIGGERED] add_calendar_event(title='{title}', date_str='{date_str}', time_str='{time_str}')"
    )
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, perform_add_calendar_event, title, date_str, time_str, duration_mins, location
    )


@llm.function_tool(
    name="delete_calendar_event",
    description="Remove an event from calendar by Event ID.",
)
async def delete_calendar_event(event_id: int) -> str:
    logger.info(f"[LIA CALENDAR TOOL TRIGGERED] delete_calendar_event(event_id={event_id})")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_delete_calendar_event, event_id)
