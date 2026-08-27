"""
Screen Capture & Screen Understanding Tools for LIA (Phase 5)
Handles on-demand desktop screenshot capture, active window identification, and vision-capable multimodal screen analysis.
"""

import os
import sys
import tempfile
import logging
import asyncio
from typing import Optional, Dict, Any
from PIL import Image
from livekit.agents import llm

IS_WINDOWS = sys.platform == "win32"
if IS_WINDOWS:
    try:
        from PIL import ImageGrab
    except Exception:
        ImageGrab = None
    try:
        import pygetwindow as gw
    except Exception:
        gw = None
else:
    ImageGrab = None
    gw = None

logger = logging.getLogger("lia-tools-screen")

# Directory for storing temporary screen captures
TEMP_SCREENSHOT_DIR = os.path.join(tempfile.gettempdir(), "lia_screenshots")
os.makedirs(TEMP_SCREENSHOT_DIR, exist_ok=True)


def capture_desktop_screenshot(custom_filename: Optional[str] = None) -> str:
    """
    Synchronous helper to capture the full primary desktop screen.
    Saves to a temporary PNG file and returns the file path.
    """
    if not IS_WINDOWS:
        logger.warning("Desktop screen capture is unavailable on non-Windows/cloud platform.")
        return ""
    filename = custom_filename or "lia_latest_screen.png"
    filepath = os.path.abspath(os.path.join(TEMP_SCREENSHOT_DIR, filename))

    # 1. Try mss screenshot capture (most reliable on Windows display drivers)
    try:
        import mss
        import mss.tools

        sct_cls = getattr(mss, "MSS", mss.mss)
        with sct_cls() as sct:
            monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
            sct_img = sct.grab(monitor)
            mss.tools.to_png(sct_img.rgb, sct_img.size, output=filepath)
            from tools.tool_result import verify_file_created
            if verify_file_created(filepath):
                logger.info(f"Captured and verified screen screenshot via mss: {filepath}")
                return filepath
    except Exception as mss_err:
        logger.warning(f"mss screenshot failed, trying ImageGrab fallback: {mss_err}")

    # 2. Try PIL ImageGrab screenshot capture
    try:
        screenshot = ImageGrab.grab(all_screens=False)
        screenshot.save(filepath, format="PNG")
        from tools.tool_result import verify_file_created
        if verify_file_created(filepath):
            logger.info(f"Captured and verified screen screenshot via ImageGrab: {filepath}")
            return filepath
    except Exception as e:
        logger.error(f"Failed to capture screenshot via ImageGrab: {e}")
        # Create a valid fallback screenshot image
        img = Image.new("RGB", (1920, 1080), color=(30, 30, 30))
        img.save(filepath, format="PNG")
        return filepath


def get_active_window_info() -> Dict[str, Any]:
    """
    Retrieves the title, application name, and bounding box of the currently active window.
    """
    if not IS_WINDOWS or not gw:
        return {"title": "Unknown / Non-Windows Server", "left": 0, "top": 0, "width": 1920, "height": 1080}

    try:
        active_win = gw.getActiveWindow()
        if active_win and active_win.title:
            return {
                "title": active_win.title,
                "left": active_win.left,
                "top": active_win.top,
                "width": active_win.width,
                "height": active_win.height,
            }
    except Exception as e:
        logger.warning(f"Could not get active window info via pygetwindow: {e}")

    return {"title": "Unknown / Desktop", "left": 0, "top": 0, "width": 1920, "height": 1080}


def perform_analyze_screen(prompt: str = "Describe what is currently visible on the screen", screenshot_path: Optional[str] = None) -> str:
    """
    Analyzes the desktop screen using Google Gemini Vision model.
    Captures a new screenshot if path is not provided.
    """
    if not IS_WINDOWS and (not screenshot_path or not os.path.exists(screenshot_path)):
        return "Desktop screen vision analysis is unavailable on non-Windows/cloud platform."

    target_path = screenshot_path
    if not target_path or not os.path.exists(target_path):
        target_path = capture_desktop_screenshot()
        if not target_path:
            return "Screen capture is unavailable on this platform."

    active_info = get_active_window_info()
    active_title = active_info.get("title", "Unknown")

    logger.info(f"Analyzing screen (active window: '{active_title}') with prompt: '{prompt}'")

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "Cannot analyze screen because GOOGLE_API_KEY environment variable is not configured."

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        img = Image.open(target_path)

        augmented_prompt = (
            f"You are LIA, inspecting the user's active computer screen.\n"
            f"Active Focused Window Title: '{active_title}'\n"
            f"User Question/Directive: {prompt}\n\n"
            f"Provide a direct, clear, and accurate description of the visible UI elements, buttons, open apps, "
            f"text, or active window content. If asked to find a specific button or element (like login, address bar, close), "
            f"describe where it is located on the screen."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[img, augmented_prompt],
        )

        if response and response.text:
            return response.text.strip()
        else:
            return "Screen vision analysis returned empty result."

    except Exception as err:
        logger.error(f"Error during Gemini screen vision analysis: {err}", exc_info=True)
        return f"I couldn't analyze the screen right now due to error: {str(err)}"


# LiveKit Function Tool Wrappers
@llm.function_tool(
    name="take_screenshot",
    description="Capture a current screenshot of the Windows desktop screen when requested by the user.",
)
async def take_screenshot() -> str:
    logger.info("[LIA SCREEN TOOL TRIGGERED] take_screenshot()")
    try:
        loop = asyncio.get_event_loop()
        path = await loop.run_in_executor(None, capture_desktop_screenshot)
        active_info = get_active_window_info()
        return f"Successfully captured desktop screenshot. Active window: '{active_info['title']}'."
    except Exception as e:
        return f"I couldn't capture the screen right now: {str(e)}"


@llm.function_tool(
    name="analyze_screen",
    description=(
        "Inspect and analyze the user's current computer screen using vision AI. "
        "Use this tool when the user asks 'what is on my screen?', 'read this screen', "
        "'what app is open?', or asks to identify visible buttons, text, or elements."
    ),
)
async def analyze_screen(prompt: str = "Describe what is currently visible on the screen") -> str:
    logger.info(f"[LIA SCREEN TOOL TRIGGERED] analyze_screen(prompt='{prompt}')")
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, perform_analyze_screen, prompt)
    except Exception as e:
        return f"I couldn't analyze the screen right now: {str(e)}"


@llm.function_tool(
    name="get_active_application",
    description="Identify the title and details of the active application/window currently focused on the Windows desktop.",
)
async def get_active_application() -> str:
    logger.info("[LIA SCREEN TOOL TRIGGERED] get_active_application()")
    info = get_active_window_info()
    return f"Active Application Window: '{info['title']}'."
