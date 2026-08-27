"""
Controlled Keyboard Automation Tools for LIA (Phase 5)
Handles text typing, key pressing, and key combination shortcuts with parameter validation.
"""

import sys
import logging
import asyncio
from typing import List
from livekit.agents import llm

logger = logging.getLogger("lia-tools-keyboard")

if sys.platform == "win32":
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.1
    except Exception:
        pyautogui = None
else:
    pyautogui = None

# Allowed standard keys for press_key and press_hotkey
ALLOWED_KEYS = {
    "enter", "return", "esc", "escape", "tab", "space", "backspace", "delete",
    "up", "down", "left", "right", "home", "end", "pageup", "pagedown",
    "ctrl", "alt", "shift", "win", "cmd", "capslock",
    "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12",
}
# Add single letters and numbers to allowed set
for char in "abcdefghijklmnopqrstuvwxyz0123456789":
    ALLOWED_KEYS.add(char)


def perform_type_text(text: str) -> str:
    """Synchronous helper to type text via PyAutoGUI."""
    if not pyautogui:
        return "Keyboard control is unavailable on non-Windows/headless OS."
    cleaned = text.strip()
    if not cleaned:
        return "Text to type was empty."

    logger.info(f"Typing text (len={len(cleaned)})")
    try:
        pyautogui.write(cleaned, interval=0.03)
        return f"Typed text into active window."
    except Exception as e:
        logger.error(f"Error typing text: {e}")
        return f"I couldn't type text: {str(e)}"


def perform_press_key(key_name: str) -> str:
    """Synchronous helper to press a single validated key."""
    if not pyautogui:
        return "Keyboard control is unavailable on non-Windows/headless OS."
    cleaned = key_name.strip().lower()

    if cleaned == "esc":
        cleaned = "escape"
    elif cleaned == "return":
        cleaned = "enter"

    if cleaned not in ALLOWED_KEYS:
        return f"Key '{key_name}' is not in the validated allowed keys list."

    logger.info(f"Pressing key: '{cleaned}'")
    try:
        pyautogui.press(cleaned)
        return f"Pressed key '{cleaned.title()}'."
    except Exception as e:
        logger.error(f"Error pressing key '{cleaned}': {e}")
        return f"I couldn't press key '{key_name}': {str(e)}"


def perform_press_hotkey(shortcut: str) -> str:
    """
    Synchronous helper to press key combination shortcut.
    Example: 'ctrl+c', 'ctrl+v', 'alt+tab', 'ctrl+a'.
    """
    if not pyautogui:
        return "Keyboard control is unavailable on non-Windows/headless OS."
    cleaned = shortcut.strip().lower()
    raw_keys = [k.strip() for k in cleaned.replace("-", "+").split("+") if k.strip()]

    valid_keys: List[str] = []
    for k in raw_keys:
        norm = "escape" if k in ["esc", "escape"] else ("enter" if k in ["return", "enter"] else k)
        if norm not in ALLOWED_KEYS:
            return f"Key '{k}' in shortcut '{shortcut}' is not allowed."
        valid_keys.append(norm)

    if not valid_keys:
        return "Invalid key shortcut provided."

    logger.info(f"Pressing hotkey shortcut: {valid_keys}")
    try:
        pyautogui.hotkey(*valid_keys)
        return f"Pressed hotkey shortcut {' + '.join([vk.title() for vk in valid_keys])}."
    except Exception as e:
        logger.error(f"Error pressing hotkey '{shortcut}': {e}")
        return f"I couldn't press shortcut '{shortcut}': {str(e)}"


# LiveKit Function Tool Wrappers
@llm.function_tool(
    name="type_text",
    description="Type text into the currently focused window or input field on the Windows desktop.",
)
async def type_text(text: str) -> str:
    logger.info(f"[LIA KEYBOARD TOOL TRIGGERED] type_text(text='{text}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_type_text, text)


@llm.function_tool(
    name="press_key",
    description="Press a single keyboard key (e.g., 'enter', 'escape', 'tab', 'space', 'backspace', 'up', 'down').",
)
async def press_key(key: str) -> str:
    logger.info(f"[LIA KEYBOARD TOOL TRIGGERED] press_key(key='{key}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_press_key, key)


@llm.function_tool(
    name="press_hotkey",
    description="Press keyboard combination shortcut such as 'ctrl+c' (copy), 'ctrl+v' (paste), 'ctrl+a' (select all), 'alt+tab'.",
)
async def press_hotkey(shortcut: str) -> str:
    logger.info(f"[LIA KEYBOARD TOOL TRIGGERED] press_hotkey(shortcut='{shortcut}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_press_hotkey, shortcut)
