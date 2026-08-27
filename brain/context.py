"""
Context Manager Engine for LIA (Phase 10 Context-Aware Conversational System)
Tracks bounded short-term conversation turns, active multi-turn tasks, reference resolution state,
device context, application context, browser context, media context, person context, language,
conversation mode, and error context with automatic TTL expiration and summarization.
NEVER stores sensitive authentication credentials, passwords, or API keys.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from collections import deque

logger = logging.getLogger("lia-context-engine")

# Bounded context window limits
MAX_RECENT_TURNS = 15
DEFAULT_CONTEXT_TTL = 300.0  # 5 minutes context expiration TTL


class LIAContextManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LIAContextManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, ttl_seconds: float = DEFAULT_CONTEXT_TTL):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self.ttl_seconds = ttl_seconds
        self.clear_all()

    def clear_all(self):
        """Resets all context fields to clean defaults."""
        self._turns: deque = deque(maxlen=MAX_RECENT_TURNS)
        self._last_interaction_time: float = time.time()
        
        # State tracking
        self.current_intent: str = "ai_answer"
        self.previous_intent: str = "none"
        self.current_device: str = "desktop"  # "desktop" or "mobile"
        self.current_application: str = "none"  # e.g., "YouTube", "Chrome", "Notepad"
        self.current_language: str = "English"  # "English", "Tamil", "Tanglish"
        self.conversation_mode: str = "ACTIVE"  # "ACTIVE", "ONE_SHOT", "WAKE_WORD", "PUSH_TO_TALK"
        self.privacy_mode: bool = False  # Privacy Mode ON/OFF
        self.screen_assist_mode: bool = False  # Real-time Screen Assist Mode ON/OFF
        
        # Multi-turn Active Task State
        self.active_task: Dict[str, Any] = {
            "name": "none",
            "status": "idle",
            "query": "",
            "results": [],
            "selected_index": -1,
            "selected_item": None,
            "timestamp": time.time()
        }
        
        # Browser Context State
        self.current_browser: Dict[str, Any] = {
            "current_url": "",
            "previous_url": "",
            "page_title": "",
            "search_query": "",
            "search_results": [],
            "selected_result_index": -1,
            "selected_result": None,
            "page_summary": ""
        }

        # Media Context State
        self.current_media: Dict[str, Any] = {
            "title": "",
            "artist": "",
            "album": "",
            "status": "stopped",  # "playing", "paused", "stopped"
            "volume": 70,
            "source": "YouTube",
            "track_index": 0,
            "results": []
        }

        # Person / Communication Context State
        self.current_person: Dict[str, Any] = {
            "name": "",
            "phone": "",
            "action": "",
            "prepared_message": "",
            "confirmed": False
        }

        # Tool Execution & Error Context State
        self.previous_tool: str = "none"
        self.previous_tool_result: Any = None
        self.last_error: Optional[Dict[str, Any]] = None
        self.pending_action: Optional[Dict[str, Any]] = None
        self.completed_actions: List[Dict[str, Any]] = []

        # Entity Registry (Phase 11 Advanced Context Engine)
        self.entity_registry: Dict[str, List[Dict[str, Any]]] = {
            "applications": [],  # [{"name": "Chrome", "metadata": {...}}]
            "files": [],         # [{"name": "server.py", "path": "/path/server.py"}]
            "web": [],           # [{"title": "React Tutorial", "url": "..."}]
            "coding": []         # [{"type": "function", "name": "process_request", "file": "orchestrator.py"}]
        }
        self.resolution_confidence: str = "HIGH"  # "HIGH", "MEDIUM", "LOW"

    def reset_task_context(self):
        """Clears short-term task and entity context without removing long-term memory."""
        logger.info("Resetting short-term task context.")
        self.active_task = {
            "name": "none",
            "status": "idle",
            "query": "",
            "results": [],
            "selected_index": -1,
            "selected_item": None,
            "timestamp": time.time()
        }
        self.current_browser["search_results"] = []
        self.current_browser["selected_result_index"] = -1
        self.current_browser["selected_result"] = None
        self.entity_registry = {"applications": [], "files": [], "web": [], "coding": []}
        self.resolution_confidence = "HIGH"

    def track_entity(self, category: str, name: str, metadata: Optional[Dict[str, Any]] = None):
        """Registers a recently mentioned entity with category and metadata."""
        if category not in self.entity_registry:
            self.entity_registry[category] = []
        entry = {"name": name, "metadata": metadata or {}, "timestamp": time.time()}
        # De-duplicate
        self.entity_registry[category] = [e for e in self.entity_registry[category] if e.get("name") != name]
        self.entity_registry[category].insert(0, entry)
        # Limit category history to 10 entities
        self.entity_registry[category] = self.entity_registry[category][:10]

    def check_expiration(self):
        """Checks context TTL and expires stale task/browser state if inactive."""
        now = time.time()
        if now - self._last_interaction_time > self.ttl_seconds:
            logger.info("Context TTL expired. Resetting task and browser session context.")
            self.active_task = {
                "name": "none",
                "status": "idle",
                "query": "",
                "results": [],
                "selected_index": -1,
                "selected_item": None,
                "timestamp": now
            }
            self.current_browser["search_results"] = []
            self.current_browser["selected_result_index"] = -1
            self.current_browser["selected_result"] = None
        self._last_interaction_time = now

    def add_turn(self, role: str, content: str, intent: str = "ai_answer", tool_used: str = None, tool_result: Any = None):
        """Appends a new interaction turn to bounded context history."""
        self.check_expiration()
        self._last_interaction_time = time.time()
        
        # Detect language
        detected_lang = self._detect_language(content)
        if detected_lang:
            self.current_language = detected_lang

        turn_entry = {
            "role": role,
            "content": content,
            "intent": intent,
            "tool_used": tool_used,
            "tool_result": tool_result,
            "language": self.current_language,
            "timestamp": time.time()
        }
        self._turns.append(turn_entry)
        
        self.previous_intent = self.current_intent
        self.current_intent = intent

    def _detect_language(self, text: str) -> Optional[str]:
        """Utility to detect English, Tamil, or Tanglish phrases."""
        t_clean = text.lower()
        if any(w in t_clean for w in ["sollu", "pannu", "idha", "paaru", "la", "vanakkam", "yenna"]):
            if any(w in t_clean for w in ["english", "explain", "simple", "okay", "tell"]):
                return "Tanglish"
            return "Tamil"
        elif any('\u0b80' <= c <= '\u0bff' for c in text):
            return "Tamil"
        elif "tanglish" in t_clean:
            return "Tanglish"
        return None

    def get_recent_turns(self, count: int = 5) -> List[Dict[str, Any]]:
        """Returns recent turns up to specified count."""
        return list(self._turns)[-count:]

    def set_active_task(self, name: str, query: str = "", results: List[Any] = None, status: str = "active"):
        """Sets active multi-turn task details."""
        self.check_expiration()
        self.active_task = {
            "name": name,
            "status": status,
            "query": query,
            "results": results or [],
            "selected_index": -1,
            "selected_item": None,
            "timestamp": time.time()
        }

    def select_task_result(self, index: int) -> Optional[Any]:
        """Selects a result item by 0-indexed integer or relative offset."""
        results = self.active_task.get("results") or self.current_browser.get("search_results") or self.current_media.get("results")
        if not results:
            return None
        
        if index < 0:
            index = len(results) + index
        
        if 0 <= index < len(results):
            selected = results[index]
            self.active_task["selected_index"] = index
            self.active_task["selected_item"] = selected
            
            # Synchronize browser selection if applicable
            if self.current_browser.get("search_results"):
                self.current_browser["selected_result_index"] = index
                self.current_browser["selected_result"] = selected
                if isinstance(selected, dict):
                    self.current_browser["previous_url"] = self.current_browser.get("current_url", "")
                    self.current_browser["current_url"] = selected.get("url", selected.get("link", ""))
                    self.current_browser["page_title"] = selected.get("title", "")
            return selected
        return None

    def set_media_context(self, title: str = "", artist: str = "", status: str = "playing", volume: int = None, results: List[Any] = None):
        """Updates current media playback state."""
        self.check_expiration()
        if title: self.current_media["title"] = title
        if artist: self.current_media["artist"] = artist
        if status: self.current_media["status"] = status
        if volume is not None: self.current_media["volume"] = volume
        if results is not None: self.current_media["results"] = results

    def set_person_context(self, name: str, phone: str = "", action: str = "message", prepared_message: str = ""):
        """Updates current person/communication context."""
        self.check_expiration()
        self.current_person = {
            "name": name,
            "phone": phone,
            "action": action,
            "prepared_message": prepared_message,
            "confirmed": False
        }

    def set_last_error(self, tool: str, message: str, step_text: str = ""):
        """Stores execution failure for retry support ('try again')."""
        self.last_error = {
            "tool": tool,
            "message": message,
            "step_text": step_text,
            "timestamp": time.time()
        }

    def get_summary(self) -> Dict[str, Any]:
        """Provides a complete summary snapshot of current context state."""
        return {
            "current_device": self.current_device,
            "current_application": self.current_application,
            "current_language": self.current_language,
            "active_task": self.active_task,
            "current_browser": self.current_browser,
            "current_media": self.current_media,
            "current_person": self.current_person,
            "last_error": self.last_error,
            "conversation_mode": self.conversation_mode,
            "recent_turns_count": len(self._turns)
        }


_global_context_manager = None


def get_context_manager() -> LIAContextManager:
    global _global_context_manager
    if _global_context_manager is None:
        _global_context_manager = LIAContextManager()
    return _global_context_manager
