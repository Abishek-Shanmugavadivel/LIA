"""
LiveKit Function Tools for LIA Long-Term Memory (Phase 6)
Exposes memory management to LIA agent session.
"""

import logging
import asyncio
from typing import Optional
from livekit.agents import llm
from memory.manager import MemoryManager
from memory.retrieval import MemoryRetrieval

logger = logging.getLogger("lia-tools-memory")

_memory_manager = MemoryManager()
_memory_retrieval = MemoryRetrieval(_memory_manager)


def _sync_remember(key: str, value: str, category: str = "general") -> str:
    return _memory_manager.save_memory(key=key, value=value, category=category)


def _sync_recall(query: str) -> str:
    results = _memory_manager.search_memory(query=query, limit=5)
    if not results:
        return f"I could not find any stored memories matching '{query}'."
    return _memory_retrieval.format_memory_response(results)


def _sync_list_memories(category: Optional[str] = None) -> str:
    results = _memory_manager.list_memories(category=category, limit=15)
    if not results:
        cat_str = f" in category '{category}'" if category else ""
        return f"No memories stored yet{cat_str}."
    return _memory_retrieval.format_memory_response(results)


def _sync_forget(key_or_query: str) -> str:
    return _memory_manager.delete_memory(key_or_query)


@llm.function_tool(
    name="remember_information",
    description=(
        "Save user preference, project detail, fact, reminder, or context into LIA's persistent long-term memory. "
        "Key should be concise title (e.g. 'user_portfolio', 'explanation_preference', 'github_profile'). "
        "Value is details to remember. Category can be 'preference', 'project', 'info', 'reminder', or 'general'."
    ),
)
async def remember_information(key: str, value: str, category: str = "general") -> str:
    logger.info(f"[LIA MEMORY TOOL TRIGGERED] remember_information(key='{key}', value='{value}', cat='{category}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_remember, key, value, category)


@llm.function_tool(
    name="recall_memory",
    description="Search and retrieve stored long-term memories about the user, preferences, past facts, or projects using a search query.",
)
async def recall_memory(query: str) -> str:
    logger.info(f"[LIA MEMORY TOOL TRIGGERED] recall_memory(query='{query}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_recall, query)


@llm.function_tool(
    name="list_all_memories",
    description="List all stored long-term memories saved across sessions, optionally filtered by category.",
)
async def list_all_memories(category: Optional[str] = None) -> str:
    logger.info(f"[LIA MEMORY TOOL TRIGGERED] list_all_memories(category='{category}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_list_memories, category)


@llm.function_tool(
    name="forget_memory",
    description="Delete or forget a stored long-term memory matching a key or topic.",
)
async def forget_memory(key_or_query: str) -> str:
    logger.info(f"[LIA MEMORY TOOL TRIGGERED] forget_memory(key_or_query='{key_or_query}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_forget, key_or_query)
