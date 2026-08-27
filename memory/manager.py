"""
Memory Manager for LIA Long-Term Memory (Phase 6)
Handles CRUD operations, sensitive information filtering, and categorization.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from memory.database import get_db_connection

logger = logging.getLogger("lia-memory-manager")

# Patterns matching sensitive keywords or credentials to filter out from memory
SENSITIVE_PATTERNS = [
    r"password",
    r"passwd",
    r"api[_-]?key",
    r"secret",
    r"token",
    r"auth[_-]?token",
    r"bearer\s+[a-zA-Z0-9\._\-]+",
    r"credit[_-]?card",
    r"cvv",
    r"ssn",
    r"private[_-]?key",
]


class MemoryManager:
    """
    Manages long-term memories in SQLite DB.
    Enforces security, memory categorization, and CRUD operations.
    """

    def __init__(self, db_file: Optional[str] = None) -> None:
        self.db_file = db_file

    def _is_sensitive(self, text: str) -> bool:
        """Returns True if text contains sensitive credential patterns."""
        combined = text.lower()
        for pattern in SENSITIVE_PATTERNS:
            if re.search(pattern, combined):
                return True
        return False

    def save_memory(self, key: str, value: str, category: str = "general", importance: int = 1) -> str:
        """
        Saves or updates a memory entry.
        Filters out sensitive info automatically.
        """
        cleaned_key = key.strip()
        cleaned_val = value.strip()
        cleaned_cat = category.strip().lower() or "general"

        if not cleaned_key or not cleaned_val:
            return "Cannot save memory with empty key or value."

        if self._is_sensitive(cleaned_key) or self._is_sensitive(cleaned_val):
            logger.warning(f"Prevented saving memory due to sensitive content filter (key: '{cleaned_key}')")
            return "Security policy prevents storing passwords, tokens, API keys, or sensitive credentials in memory."

        conn = get_db_connection(self.db_file)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO memories (category, key, value, importance, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(key) DO UPDATE SET
                        category = excluded.category,
                        value = excluded.value,
                        importance = excluded.importance,
                        updated_at = CURRENT_TIMESTAMP;
                    """,
                    (cleaned_cat, cleaned_key, cleaned_val, importance),
                )
            logger.info(f"Memory saved successfully: key='{cleaned_key}', category='{cleaned_cat}'")
            return f"Remembered that {cleaned_key}: {cleaned_val}."
        except Exception as e:
            logger.error(f"Error saving memory key='{cleaned_key}': {e}", exc_info=True)
            return f"Could not save memory due to database error: {str(e)}"
        finally:
            conn.close()

    def get_memory(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieves a specific memory by key."""
        cleaned_key = key.strip()
        conn = get_db_connection(self.db_file)
        try:
            row = conn.execute(
                "SELECT id, category, key, value, importance, created_at, updated_at FROM memories WHERE LOWER(key) = LOWER(?);",
                (cleaned_key,),
            ).fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()

    def search_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Searches memories matching key, value, or category.
        """
        cleaned_query = query.strip()
        if not cleaned_query:
            return []

        pattern = f"%{cleaned_query}%"
        conn = get_db_connection(self.db_file)
        try:
            rows = conn.execute(
                """
                SELECT id, category, key, value, importance, created_at, updated_at
                FROM memories
                WHERE key LIKE ? OR value LIKE ? OR category LIKE ?
                ORDER BY importance DESC, updated_at DESC
                LIMIT ?;
                """,
                (pattern, pattern, pattern, limit),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def list_memories(self, category: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Lists all stored memories, optionally filtered by category."""
        conn = get_db_connection(self.db_file)
        try:
            if category:
                rows = conn.execute(
                    """
                    SELECT id, category, key, value, importance, created_at, updated_at
                    FROM memories
                    WHERE LOWER(category) = LOWER(?)
                    ORDER BY updated_at DESC
                    LIMIT ?;
                    """,
                    (category.strip(), limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, category, key, value, importance, created_at, updated_at
                    FROM memories
                    ORDER BY updated_at DESC
                    LIMIT ?;
                    """,
                    (limit,),
                ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def delete_memory(self, key_or_query: str) -> str:
        """Deletes a memory matching key or key query."""
        cleaned = key_or_query.strip()
        if not cleaned:
            return "Please specify what memory key or query to forget."

        conn = get_db_connection(self.db_file)
        try:
            with conn:
                cursor = conn.execute(
                    "DELETE FROM memories WHERE LOWER(key) = LOWER(?) OR LOWER(key) LIKE LOWER(?);",
                    (cleaned, f"%{cleaned}%"),
                )
                deleted = cursor.rowcount

            if deleted > 0:
                logger.info(f"Deleted {deleted} memory record(s) matching '{cleaned}'")
                return f"Successfully deleted memory regarding '{cleaned}'."
            else:
                return f"No memory found matching '{cleaned}'."
        except Exception as e:
            logger.error(f"Error deleting memory for '{cleaned}': {e}")
            return f"Could not delete memory: {str(e)}"
        finally:
            conn.close()

    def clear_all(self) -> str:
        """Clears all stored memories (used in tests or user reset)."""
        conn = get_db_connection(self.db_file)
        try:
            with conn:
                conn.execute("DELETE FROM memories;")
            return "Cleared all long-term memories."
        finally:
            conn.close()


_global_memory_manager: Optional[MemoryManager] = None


def get_memory_manager(db_file: Optional[str] = None) -> MemoryManager:
    global _global_memory_manager
    if _global_memory_manager is None:
        _global_memory_manager = MemoryManager(db_file=db_file)
    return _global_memory_manager
