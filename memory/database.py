"""
SQLite Database Connection and Schema Management for LIA Long-Term Memory (Phase 6–9)
Includes tables for Memories, Reminders, and Calendar Events.
"""

import os
import sqlite3
import logging
from typing import Optional

logger = logging.getLogger("lia-memory-db")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lia_memory.db")


def get_db_connection(db_file: Optional[str] = None) -> sqlite3.Connection:
    """Returns a connection to the SQLite database with row factory configured."""
    target = db_file or DB_PATH
    conn = sqlite3.connect(target, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_file: Optional[str] = None) -> None:
    """Initializes the SQLite schema for memories, reminders, and calendar events."""
    conn = get_db_connection(db_file)
    try:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL DEFAULT 'general',
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    importance INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(key) ON CONFLICT REPLACE
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key);"
            )

            # Reminders Table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    datetime_str TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            # Calendar Events Table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS calendar_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    date_str TEXT NOT NULL,
                    time_str TEXT NOT NULL,
                    duration_mins INTEGER DEFAULT 60,
                    location TEXT DEFAULT 'Online/TBD',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
        logger.info(f"Database initialized successfully at '{db_file or DB_PATH}'.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise
    finally:
        conn.close()


# Ensure database and schema exist on import
init_db()
