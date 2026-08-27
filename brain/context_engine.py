"""
Unified Context Engine for LIA (JARVIS Next Core Upgrade)
Unifies Conversation Context, Task Context, Application/Window Context,
Browser/Tab Context, Screen State, and Reference Resolution Engine into a single snapshot.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from brain.context import get_context_manager, LIAContextManager
from brain.reference_resolver import ReferenceResolver

logger = logging.getLogger("lia-context-engine")


class ContextEngine:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ContextEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self.ctx: LIAContextManager = get_context_manager()
        self.resolver = ReferenceResolver(self.ctx)

        # Extended Context State Tracking
        self.current_window: str = "Desktop"
        self.current_browser_tab: Dict[str, Any] = {"title": "", "url": "", "index": 0}
        self.recent_actions: List[Dict[str, Any]] = []
        self.last_clicked_element: Optional[Dict[str, Any]] = None
        self.last_typed_text: str = ""
        self.last_opened_file: str = ""
        self.current_screen_state: Dict[str, Any] = {"active_window": "", "elements": [], "text_summary": ""}
        self.pending_workflow: Optional[Dict[str, Any]] = None
        self.failed_actions: List[Dict[str, Any]] = []

    def record_action(self, action_name: str, target: str, result: Any, success: bool = True):
        """Records an action into recent_actions history and updates relevant tracking fields."""
        action_entry = {
            "action": action_name,
            "target": target,
            "result": result,
            "success": success,
            "timestamp": time.time()
        }
        self.recent_actions.insert(0, action_entry)
        self.recent_actions = self.recent_actions[:20]

        if success:
            self.ctx.completed_actions.insert(0, action_entry)
            self.ctx.completed_actions = self.ctx.completed_actions[:20]
        else:
            self.failed_actions.insert(0, action_entry)
            self.failed_actions = self.failed_actions[:20]
            self.ctx.set_last_error(action_name, str(result), target)

    def record_click(self, element_name: str, location: Tuple[int, int]):
        """Tracks the last clicked element."""
        self.last_clicked_element = {"label": element_name, "location": location, "timestamp": time.time()}
        self.record_action("click", element_name, f"Clicked at {location}", success=True)

    def record_type(self, text: str, field_name: str = "input"):
        """Tracks last typed text."""
        self.last_typed_text = text
        self.record_action("type", field_name, f"Typed '{text}'", success=True)

    def record_opened_file(self, file_path: str):
        """Tracks last opened file."""
        self.last_opened_file = file_path
        self.ctx.track_entity("files", os.path.basename(file_path), {"path": file_path})
        self.record_action("open_file", file_path, "File opened", success=True)

    def update_browser_tab(self, title: str, url: str, tab_index: int = 0):
        """Updates browser tab context."""
        self.current_browser_tab = {"title": title, "url": url, "index": tab_index, "timestamp": time.time()}
        self.ctx.current_browser["current_url"] = url
        self.ctx.current_browser["page_title"] = title

    def update_screen_state(self, active_window: str, elements: List[Dict[str, Any]], text_summary: str):
        """Updates screen state snapshot."""
        self.current_screen_state = {
            "active_window": active_window,
            "elements": elements,
            "text_summary": text_summary,
            "timestamp": time.time()
        }
        self.current_window = active_window

    def resolve_reference(self, user_prompt: str) -> Dict[str, Any]:
        """Delegates reference resolution to ReferenceResolver and returns context-enriched dictionary."""
        return self.resolver.resolve(user_prompt)

    def get_full_context_snapshot(self) -> Dict[str, Any]:
        """Returns structured complete snapshot of all 20 context dimensions."""
        base_summary = self.ctx.get_summary()
        base_summary.update({
            "current_window": self.current_window,
            "current_browser_tab": self.current_browser_tab,
            "recent_actions": self.recent_actions[:5],
            "last_clicked_element": self.last_clicked_element,
            "last_typed_text": self.last_typed_text,
            "last_opened_file": self.last_opened_file,
            "current_screen_state": self.current_screen_state,
            "pending_workflow": self.pending_workflow,
            "failed_actions_count": len(self.failed_actions)
        })
        return base_summary


_global_context_engine: Optional[ContextEngine] = None


def get_context_engine() -> ContextEngine:
    global _global_context_engine
    if _global_context_engine is None:
        _global_context_engine = ContextEngine()
    return _global_context_engine
