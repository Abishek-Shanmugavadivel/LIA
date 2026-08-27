"""
Controlled Mouse Control Tools for LIA (Phase 5)
Handles mouse movement, clicking, double clicking, and right clicking with strict coordinate validation.
"""

import sys
import logging
import asyncio
from typing import Optional, Tuple
from livekit.agents import llm

logger = logging.getLogger("lia-tools-mouse")

if sys.platform == "win32":
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.1
    except Exception:
        pyautogui = None
else:
    pyautogui = None


def validate_coordinates(x: int, y: int) -> Tuple[bool, str, int, int]:
    """
    Validates target coordinates against primary screen bounds.
    Returns (is_valid, error_msg_or_ok, bounded_x, bounded_y).
    """
    if not pyautogui:
        return False, "Mouse control is unavailable on non-Windows/headless OS.", 0, 0

    screen_width, screen_height = pyautogui.size()

    if x < 0 or x > screen_width or y < 0 or y > screen_height:
        err = f"Coordinates ({x}, {y}) are outside valid screen bounds (0-{screen_width}, 0-{screen_height})."
        logger.warning(err)
        return False, err, 0, 0

    return True, "OK", x, y


def perform_move_mouse(x: int, y: int) -> str:
    """Synchronous helper to move mouse cursor to validated target coordinate."""
    valid, msg, bx, by = validate_coordinates(x, y)
    if not valid:
        return msg

    try:
        pyautogui.moveTo(bx, by, duration=0.3)
        logger.info(f"Moved mouse cursor to ({bx}, {by})")
        return f"Moved mouse pointer to position ({bx}, {by})."
    except Exception as e:
        logger.error(f"Error moving mouse cursor: {e}")
        return f"I couldn't perform that mouse action: {str(e)}"


def perform_click_mouse(x: Optional[int] = None, y: Optional[int] = None, button: str = "left", double: bool = False) -> str:
    """Synchronous helper to click mouse button at current position or validated (x, y)."""
    btn = button.lower()
    if btn not in ["left", "right", "middle"]:
        btn = "left"

    target_desc = "current position"
    if x is not None and y is not None:
        valid, msg, bx, by = validate_coordinates(x, y)
        if not valid:
            return msg
        pyautogui.moveTo(bx, by, duration=0.2)
        target_desc = f"({bx}, {by})"

    try:
        if double:
            pyautogui.doubleClick(button=btn)
            logger.info(f"Double-clicked {btn} mouse button at {target_desc}")
            return f"Double-clicked {btn} mouse button at {target_desc}."
        else:
            pyautogui.click(button=btn)
            logger.info(f"Clicked {btn} mouse button at {target_desc}")
            return f"Clicked {btn} mouse button at {target_desc}."
    except Exception as e:
        logger.error(f"Error clicking mouse: {e}")
        return f"I couldn't perform that mouse action: {str(e)}"


# LiveKit Function Tool Wrappers
@llm.function_tool(
    name="move_mouse",
    description="Move mouse cursor to specific (x, y) screen coordinates on Windows desktop.",
)
async def move_mouse(x: int, y: int) -> str:
    logger.info(f"[LIA MOUSE TOOL TRIGGERED] move_mouse({x}, {y})")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_move_mouse, x, y)


@llm.function_tool(
    name="click_mouse",
    description="Click left mouse button at current position or optional target coordinates (x, y).",
)
async def click_mouse(x: Optional[int] = None, y: Optional[int] = None) -> str:
    logger.info(f"[LIA MOUSE TOOL TRIGGERED] click_mouse(x={x}, y={y})")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_click_mouse, x, y, "left", False)


@llm.function_tool(
    name="double_click_mouse",
    description="Double-click mouse button at current position or target coordinates (x, y).",
)
async def double_click_mouse(x: Optional[int] = None, y: Optional[int] = None) -> str:
    logger.info(f"[LIA MOUSE TOOL TRIGGERED] double_click_mouse(x={x}, y={y})")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_click_mouse, x, y, "left", True)


@llm.function_tool(
    name="right_click_mouse",
    description="Right-click mouse button at current position or target coordinates (x, y).",
)
async def right_click_mouse(x: Optional[int] = None, y: Optional[int] = None) -> str:
    logger.info(f"[LIA MOUSE TOOL TRIGGERED] right_click_mouse(x={x}, y={y})")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_click_mouse, x, y, "right", False)
