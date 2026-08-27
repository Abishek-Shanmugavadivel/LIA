"""
Voice & Assistant State Machine for LIA (IDLE, LISTENING, THINKING, EXECUTING, SPEAKING, ERROR)
Provides state tracking, transition callbacks, and watchdog timeout auto-recovery.
"""

import time
import logging
import threading
from typing import Callable, List, Optional

logger = logging.getLogger("lia-state-machine")


class LIAState:
    STARTING = "STARTING"
    CONNECTED = "CONNECTED"
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    PROCESSING = "PROCESSING"
    EXECUTING = "EXECUTING"
    SPEAKING = "SPEAKING"
    SLEEPING = "SLEEPING"
    RECONNECTING = "RECONNECTING"
    ERROR = "ERROR"


class VoiceStateMachine:
    def __init__(self, initial_state: str = LIAState.IDLE, watchdog_timeout_seconds: float = 30.0):
        self._current_state = initial_state
        self._last_state_change = time.time()
        self._watchdog_timeout = watchdog_timeout_seconds
        self._lock = threading.Lock()
        self._listeners: List[Callable[[str, str], None]] = []

    def add_listener(self, callback: Callable[[str, str], None]) -> None:
        """Register a callback for state transition events callback(old_state, new_state)."""
        with self._lock:
            self._listeners.append(callback)

    def get_state(self) -> str:
        """Returns the current state after performing a watchdog check."""
        self._check_watchdog()
        with self._lock:
            return self._current_state

    def set_state(self, new_state: str) -> bool:
        """Transitions to new_state and notifies all registered listeners."""
        with self._lock:
            old_state = self._current_state
            if old_state == new_state:
                return False
            self._current_state = new_state
            self._last_state_change = time.time()
            listeners = list(self._listeners)

        logger.info(f"LIA State Transition: {old_state} -> {new_state}")
        for listener in listeners:
            try:
                listener(old_state, new_state)
            except Exception as e:
                logger.error(f"State transition listener error: {e}")
        return True

    def _check_watchdog(self) -> None:
        """Watchdog to auto-recover if stuck in an active state beyond timeout."""
        with self._lock:
            if self._current_state not in (LIAState.IDLE, LIAState.SLEEPING):
                elapsed = time.time() - self._last_state_change
                if elapsed > self._watchdog_timeout:
                    old_state = self._current_state
                    logger.warning(
                        f"Watchdog auto-recovery: LIA stuck in state '{old_state}' for {elapsed:.1f}s. Resetting to IDLE."
                    )
                    self._current_state = LIAState.IDLE
                    self._last_state_change = time.time()


_global_state_machine: Optional[VoiceStateMachine] = None


def get_state_machine() -> VoiceStateMachine:
    global _global_state_machine
    if _global_state_machine is None:
        _global_state_machine = VoiceStateMachine()
    return _global_state_machine
