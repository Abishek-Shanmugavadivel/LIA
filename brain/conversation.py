"""
Conversation Manager for LIA Phase 2
Handles in-memory conversation context, turn history, and state tracking.
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger("lia-conversation")


class ConversationManager:
    """
    Manages current conversation context for LIA.
    Keeps turn history in memory for resolving follow-up questions and pronouns.
    No persistent database storage is used in Phase 2.
    """

    def __init__(self, max_history_turns: int = 10) -> None:
        self.max_history_turns = max_history_turns
        self._history: List[Dict[str, str]] = []

    def add_user_message(self, text: str) -> None:
        """Add user turn to conversation history."""
        cleaned = text.strip()
        if cleaned:
            self._history.append({"role": "user", "content": cleaned})
            self._truncate_if_needed()

    def add_assistant_message(self, text: str) -> None:
        """Add assistant turn to conversation history."""
        cleaned = text.strip()
        if cleaned:
            self._history.append({"role": "assistant", "content": cleaned})
            self._truncate_if_needed()

    def get_history(self) -> List[Dict[str, str]]:
        """Get copy of current conversation history."""
        return list(self._history)

    def format_prompt_with_history(self, current_prompt: str) -> str:
        """
        Format system prompt with full conversation history context
        for LLM invocation.
        """
        if not self._history:
            return current_prompt

        history_str = "\n".join(
            [f"{msg['role'].capitalize()}: {msg['content']}" for msg in self._history]
        )

        return f"{current_prompt}\n\nCONVERSATION HISTORY:\n{history_str}"

    def _truncate_if_needed(self) -> None:
        """Keep only the most recent max_history_turns messages."""
        max_messages = self.max_history_turns * 2
        if len(self._history) > max_messages:
            logger.info(f"Truncating conversation history to last {max_messages} messages")
            self._history = self._history[-max_messages:]

    def clear(self) -> None:
        """Reset conversation history."""
        self._history.clear()

    @property
    def turn_count(self) -> int:
        """Return total number of turns recorded."""
        return len(self._history)
