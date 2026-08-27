"""
Global Hotkey Manager for LIA (CTRL + SHIFT + L)
Uses pynput to capture global hotkey across Windows without interfering with standard system shortcuts.
Triggers activation / toggle listening mode on first press; interrupts speaking/response on second press.
"""

import logging
import threading
from typing import Callable, Optional
from pynput import keyboard
from voice.state_machine import get_state_machine, LIAState

logger = logging.getLogger("lia-hotkey")


class LIAHotkeyManager:
    def __init__(self, on_hotkey_pressed: Optional[Callable[[], None]] = None):
        self.sm = get_state_machine()
        self.on_hotkey_pressed = on_hotkey_pressed
        self.listener: Optional[keyboard.GlobalHotKeys] = None
        self._is_active = False

    def _handle_hotkey(self):
        """Called when CTRL+SHIFT+L is pressed globally."""
        current_state = self.sm.get_state()
        logger.info(f"Global Hotkey CTRL+SHIFT+L pressed. Current state: {current_state}")

        if current_state == LIAState.IDLE:
            self.sm.set_state(LIAState.LISTENING)
            if self.on_hotkey_pressed:
                try:
                    self.on_hotkey_pressed()
                except Exception as e:
                    logger.error(f"Error in hotkey press handler: {e}")
        elif current_state in [LIAState.LISTENING, LIAState.SPEAKING, LIAState.THINKING, LIAState.EXECUTING]:
            logger.info("Global Hotkey interrupting current LIA action/response...")
            self.sm.set_state(LIAState.IDLE)

    def start(self, daemon: bool = True):
        """Starts global hotkey listener."""
        if self._is_active:
            return

        try:
            hotkeys = {
                '<ctrl>+<shift>+l': self._handle_hotkey,
                '<ctrl>+<shift>+L': self._handle_hotkey
            }
            self.listener = keyboard.GlobalHotKeys(hotkeys)
            self.listener.start()
            self._is_active = True
            logger.info("LIA Global Hotkey listener started: CTRL+SHIFT+L registered.")
        except Exception as e:
            logger.error(f"Failed to start LIA Global Hotkey listener: {e}")

    def stop(self):
        """Stops global hotkey listener."""
        if self.listener and self._is_active:
            try:
                self.listener.stop()
            except Exception:
                pass
            self._is_active = False
            logger.info("LIA Global Hotkey listener stopped.")


_global_hotkey_manager: Optional[LIAHotkeyManager] = None


def get_hotkey_manager() -> LIAHotkeyManager:
    global _global_hotkey_manager
    if _global_hotkey_manager is None:
        _global_hotkey_manager = LIAHotkeyManager()
    return _global_hotkey_manager


if __name__ == "__main__":
    import time
    print("Testing LIA Global Hotkey listener (CTRL + SHIFT + L)...")
    mgr = get_hotkey_manager()
    mgr.start(daemon=True)
    print("Hotkey listener successfully initialized and registered.")
    time.sleep(0.5)
    mgr.stop()
    print("Hotkey listener stopped cleanly.")

