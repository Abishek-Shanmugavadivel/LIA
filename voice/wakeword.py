"""
Wake Word Detection & Conversation State System for LIA JARVIS Experience (Phase 8–9)
Supports "Hey LIA", "LIA", "JARVIS", "Hey JARVIS" keyword detection, conversation state machine,
and speech interruption logic.
"""

import time
import logging
from enum import Enum
from typing import Optional, Callable

logger = logging.getLogger("lia-wakeword")

class ConversationMode(Enum):
    ACTIVE = "active"             # Continuous conversation mode
    ONE_SHOT = "one_shot"         # Single command, then wait for wake word
    WAKE_WORD = "wake_word"       # Idle waiting for wake trigger
    PUSH_TO_TALK = "push_to_talk" # Manual trigger fallback

# Supported wake word triggers (LIA & JARVIS English & Tanglish variations)
WAKE_WORDS = [
    "hey lia", "lia", "hey leah", "hello lia", "hi lia",
    "jarvis", "hey jarvis", "hello jarvis", "hi jarvis", "jarvis ai"
]

# Interruption phrases to stop ongoing speech output & emergency stop
INTERRUPT_WORDS = ["stop lia", "cancel task", "cancel mission", "emergency stop", "cancel", "stop", "okay stop", "quiet", "shut up", "wait", "hold on", "pause", "enough"]

class WakeWordDetector:
    def __init__(self, mode: ConversationMode = ConversationMode.WAKE_WORD):
        self.mode = mode
        self.is_activated = (mode == ConversationMode.ACTIVE)
        self.last_active_time = time.time()
        self.active_timeout_seconds = 60.0  # Timeout active mode to wake_word after 60s idle

    def process_transcript(self, transcript: str) -> dict:
        """
        Evaluates incoming audio transcript for wake words, interruption words, or command payloads.
        Returns state decision dict: { 'activated': bool, 'is_interruption': bool, 'cleaned_prompt': str }
        """
        text_lower = transcript.lower().strip()

        # 1. Check for user interruption command
        if any(word in text_lower for word in INTERRUPT_WORDS):
            logger.info("Interruption word detected. Stopping LIA speech output.")
            return {
                "activated": False,
                "is_interruption": True,
                "cleaned_prompt": "",
                "mode": self.mode.value
            }

        # 2. Check for Wake Word trigger
        wake_detected = False
        cleaned = transcript
        for kw in WAKE_WORDS:
            if kw in text_lower:
                wake_detected = True
                # Remove the wake word prefix to leave the core user command
                pattern_idx = text_lower.find(kw)
                cleaned = transcript[pattern_idx + len(kw):].strip(" ,.!")
                break

        if wake_detected:
            self.is_activated = True
            self.last_active_time = time.time()
            logger.info(f"Wake word detected! Activating LIA JARVIS. Prompt: '{cleaned}'")
            return {
                "activated": True,
                "is_interruption": False,
                "cleaned_prompt": cleaned if cleaned else transcript,
                "mode": self.mode.value
            }

        # 3. If currently in ACTIVE mode, check timeout
        if self.mode == ConversationMode.ACTIVE:
            if (time.time() - self.last_active_time) < self.active_timeout_seconds:
                return {
                    "activated": True,
                    "is_interruption": False,
                    "cleaned_prompt": transcript,
                    "mode": self.mode.value
                }
            else:
                logger.info("Active session timed out. Reverting to WAKE_WORD mode.")
                self.mode = ConversationMode.WAKE_WORD
                self.is_activated = False

        # 4. If in WAKE_WORD mode and no wake word detected
        if self.mode == ConversationMode.WAKE_WORD and not self.is_activated:
            return {
                "activated": False,
                "is_interruption": False,
                "cleaned_prompt": "",
                "mode": self.mode.value
            }

        return {
            "activated": self.is_activated,
            "is_interruption": False,
            "cleaned_prompt": transcript,
            "mode": self.mode.value
        }

    def set_mode(self, mode: ConversationMode):
        """Updates current conversation mode."""
        self.mode = mode
        if mode == ConversationMode.ACTIVE:
            self.is_activated = True
            self.last_active_time = time.time()
        elif mode == ConversationMode.WAKE_WORD:
            self.is_activated = False
        logger.info(f"Conversation mode changed to: {mode.value}")
