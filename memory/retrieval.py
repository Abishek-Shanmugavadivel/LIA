"""
Memory Retrieval Layer for LIA (Phase 6)
Formats retrieved memories for spoken response and LLM context synthesis.
"""

import logging
from typing import List, Dict, Any, Optional
from memory.manager import MemoryManager

logger = logging.getLogger("lia-memory-retrieval")


class MemoryRetrieval:
    """
    Retrieves and formats memories for LIA Agent context and user queries.
    """

    def __init__(self, manager: Optional[MemoryManager] = None) -> None:
        self.manager = manager or MemoryManager()

    def retrieve_relevant_context(self, query: str, limit: int = 5) -> str:
        """
        Retrieves relevant memories based on user query and formats as clean context string.
        """
        results = self.manager.search_memory(query, limit=limit)
        if not results:
            return ""

        formatted_items = []
        for item in results:
            formatted_items.append(f"- [{item['category'].upper()}] {item['key']}: {item['value']}")

        return "RELEVANT RECALLED MEMORIES:\n" + "\n".join(formatted_items)

    def format_memory_response(self, memories: List[Dict[str, Any]]) -> str:
        """
        Formats memories into natural conversational text for LIA spoken output.
        """
        if not memories:
            return "I don't have any memories saved about that."

        lines = []
        for mem in memories:
            lines.append(f"{mem['key']}: {mem['value']}")

        return "Here is what I remember:\n" + "\n".join(lines)
