"""
Reference Resolution Engine for LIA (Phase 10 Context-Aware Conversational System)
Resolves pronouns (it, this, that, him, her, them, there, here), ordinals (first one, second one, etc.),
corrections (no, not that one), follow-ups, and retries using the active LIA Context Manager.
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple
from brain.context import get_context_manager, LIAContextManager

logger = logging.getLogger("lia-reference-resolver")

# Ordinal text to 0-indexed integer map
ORDINAL_MAP = {
    "first": 0, "1st": 0, "one": 0,
    "second": 1, "2nd": 1, "two": 1,
    "third": 2, "3rd": 2, "three": 2,
    "fourth": 3, "4th": 3, "four": 3,
    "fifth": 4, "5th": 4, "five": 4,
    "last": -1, "final": -1
}


class ReferenceResolver:
    def __init__(self, context_mgr: Optional[LIAContextManager] = None):
        self.ctx = context_mgr or get_context_manager()

    def resolve(self, user_input: str) -> Dict[str, Any]:
        """
        Main resolution entrypoint.
        Analyzes user input, inspects context, resolves pronouns, ordinals, corrections, and retries.
        Returns a dictionary containing resolved prompt, intent suggestion, target entity, and index if applicable.
        """
        text = user_input.strip()
        t_lower = text.lower()

        resolved_info = {
            "original_prompt": text,
            "resolved_prompt": text,
            "resolved_entity": None,
            "selected_index": None,
            "intent_override": None,
            "is_correction": False,
            "is_retry": False,
            "person_target": None,
            "device_target": None,
            "app_target": None
        }

        # 0. Check for Context Reset ("forget what we're doing", "start a new task", "reset context", "new task")
        if any(kw in t_lower for kw in ["forget what we're doing", "forget what we are doing", "start a new task", "reset current context", "reset context", "new task"]):
            self.ctx.reset_task_context()
            resolved_info["intent_override"] = "context_reset"
            resolved_info["resolved_prompt"] = "Task context reset."
            logger.info("Executed task context reset upon user request.")
            return resolved_info

        # 1. Check for Retry ("try again", "retry", "do it again")
        if any(kw in t_lower for kw in ["try again", "retry", "do it again", "run again"]):
            if self.ctx.last_error:
                resolved_info["is_retry"] = True
                resolved_info["resolved_prompt"] = self.ctx.last_error.get("step_text", text)
                resolved_info["intent_override"] = "retry"
                logger.info(f"Resolved retry command to previous failed step: '{resolved_info['resolved_prompt']}'")
                return resolved_info

        # 2. Check for Correction ("no, the second one", "not that one", "i meant the second one")
        if any(kw in t_lower for kw in ["no,", "not that", "i meant", "wrong one", "use the other", "the other file"]):
            resolved_info["is_correction"] = True

        # 3. Resolve Person Pronouns ("him", "her", "them", "he", "she", "they")
        if any(p in t_lower for p in ["him", "her", "them", "he ", "she "]):
            person_name = self.ctx.current_person.get("name")
            if person_name:
                resolved_info["person_target"] = person_name
                substituted = re.sub(r'\b(him|her|them)\b', person_name, text, flags=re.IGNORECASE)
                resolved_info["resolved_prompt"] = substituted
                logger.info(f"Resolved pronoun 'him/her' -> '{person_name}'")

        # 4. Resolve Ordinal Result Selection ("first one", "second one", "third one", "play the second one", "open the first one", "previous one", "next one")
        ordinal_index = self._extract_ordinal_index(t_lower)
        if ordinal_index is not None:
            resolved_info["selected_index"] = ordinal_index
            selected_item = self.ctx.select_task_result(ordinal_index)
            resolved_info["resolved_entity"] = selected_item
            logger.info(f"Resolved ordinal index {ordinal_index} -> selected item: {selected_item}")

        # 5. Resolve Pronouns & Demonstratives ("it", "this", "that", "this one", "that one", "the backend one", "the one on the left", "that website", "that file", "that window")
        if any(kw in t_lower for kw in ["it", "this", "that", "same", "again", "left", "right", "backend", "file", "window"]):
            resolved_entity = self._resolve_demonstratives(t_lower)
            if resolved_entity:
                resolved_info["resolved_entity"] = resolved_entity
                logger.info(f"Resolved demonstrative in '{text}' -> '{resolved_entity}'")

        # 6. Evaluate Resolution Confidence Level
        if resolved_info["resolved_entity"] or resolved_info["selected_index"] is not None:
            self.ctx.resolution_confidence = "HIGH"
        elif any(kw in t_lower for kw in ["it", "that", "this", "the second one", "that one"]):
            self.ctx.resolution_confidence = "MEDIUM" if self.ctx.active_task.get("query") else "LOW"
        else:
            self.ctx.resolution_confidence = "HIGH"

        # 7. Device Context Resolution (Explicit priority vs active context)
        if "laptop" in t_lower or "computer" in t_lower or "desktop" in t_lower:
            resolved_info["device_target"] = "desktop"
            self.ctx.current_device = "desktop"
        elif "phone" in t_lower or "mobile" in t_lower or "android" in t_lower:
            resolved_info["device_target"] = "mobile"
            self.ctx.current_device = "mobile"
        else:
            resolved_info["device_target"] = self.ctx.current_device

        # 8. Application Context Resolution ("YouTube", "Chrome", "WhatsApp", "Notepad", "Spotify", "VS Code")
        if "youtube" in t_lower:
            resolved_info["app_target"] = "YouTube"
            self.ctx.current_application = "YouTube"
        elif "chrome" in t_lower:
            resolved_info["app_target"] = "Chrome"
            self.ctx.current_application = "Chrome"
        elif "whatsapp" in t_lower:
            resolved_info["app_target"] = "WhatsApp"
            self.ctx.current_application = "WhatsApp"
        elif "vs code" in t_lower or "vscode" in t_lower or "code" in t_lower:
            resolved_info["app_target"] = "VS Code"
            self.ctx.current_application = "VS Code"
        else:
            resolved_info["app_target"] = self.ctx.current_application

        return resolved_info

    def _extract_ordinal_index(self, text: str) -> Optional[int]:
        """Extracts 0-indexed integer from ordinal phrases like 'second one', '1st result', 'last one'."""
        patterns = [
            r"(?:the\s+)?(first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th|last|final)\s+(?:one|result|article|item|song|video|page)?",
            r"(?:play|open|read|select|summarize)\s+(?:the\s+)?(first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th|last|final)"
        ]
        for pat in patterns:
            match = re.search(pat, text)
            if match:
                ord_str = match.group(1).lower()
                if ord_str in ORDINAL_MAP:
                    return ORDINAL_MAP[ord_str]
        return None

    def _resolve_demonstratives(self, text: str) -> Optional[Any]:
        """Resolves 'it', 'this', 'that' against active task, browser, media, or person context."""
        # 1. Media context ("play it", "make it louder", "pause it", "that song")
        if any(m_kw in text for m_kw in ["louder", "quieter", "volume", "pause", "resume", "song", "music"]):
            if self.ctx.current_media.get("title"):
                return self.ctx.current_media["title"]
        
        # 2. Browser / News article context ("summarize it", "read it", "that article", "that page", "that website")
        if any(b_kw in text for b_kw in ["summarize", "read", "explain", "article", "page", "website", "url"]):
            if self.ctx.current_browser.get("selected_result"):
                return self.ctx.current_browser["selected_result"]
            elif self.ctx.current_browser.get("current_url"):
                return self.ctx.current_browser["current_url"]
            elif self.ctx.active_task.get("selected_item"):
                return self.ctx.active_task["selected_item"]

        # 3. Person context ("tell him", "message her")
        if any(p_kw in text for p_kw in ["him", "her", "person"]):
            if self.ctx.current_person.get("name"):
                return self.ctx.current_person["name"]

        # 4. Fallback to active task selected item or query
        if self.ctx.active_task.get("selected_item"):
            return self.ctx.active_task["selected_item"]
        elif self.ctx.active_task.get("query"):
            return self.ctx.active_task["query"]

        return None
