"""
LIA Long-Term Memory Package (Phase 6)
Provides persistent storage, retrieval, and management of user preferences, facts, and project context.
"""

from memory.database import init_db, get_db_connection
from memory.manager import MemoryManager

__all__ = ["init_db", "get_db_connection", "MemoryManager"]
