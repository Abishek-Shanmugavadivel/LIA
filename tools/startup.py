"""
Desktop Startup, System Tray & Global Hotkey Helper for LIA (Phase 9)
Configures Windows startup registry/shortcuts, system tray icon management, and global hotkey listeners.
"""

import os
import sys
import logging
import asyncio
from livekit.agents import llm

logger = logging.getLogger("lia-tools-startup")


def perform_configure_startup(enable: bool = True) -> str:
    """Synchronous helper to enable/disable Windows auto-startup for LIA Assistant."""
    if sys.platform != "win32":
        return "Auto-startup configuration is only supported on Windows Desktop OS."

    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "LIA_JARVIS_Assistant"
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agent.py"))
        python_exe = sys.executable
        cmd = f'"{python_exe}" "{script_path}" dev'

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
            if enable:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, cmd)
                logger.info(f"Windows startup entry added for LIA: {cmd}")
                return "✅ LIA Desktop Startup enabled. LIA will launch automatically on Windows boot."
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                    logger.info("Windows startup entry removed for LIA.")
                    return "❌ LIA Desktop Startup disabled."
                except FileNotFoundError:
                    return "LIA Desktop Startup was not configured."
    except Exception as e:
        logger.error(f"Error configuring Windows startup: {e}")
        return f"Could not configure desktop startup: {e}"


def initialize_lia_startup() -> dict:
    """
    Step-by-step production startup manager.
    Validates configuration, initializes services, checks database & devices,
    and returns status (HEALTHY or DEGRADED) without crashing the process.
    """
    from dotenv import load_dotenv
    load_dotenv(".env")

    required_vars = ["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "GOOGLE_API_KEY"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        logger.warning(f"Startup notice: Missing configuration keys {missing}. LIA running in DEGRADED mode.")

    # Initialize DB & Health Monitor
    from health import get_health_monitor
    health_mon = get_health_monitor()
    health_status = health_mon.check_health(force_refresh=True)

    status_code = health_status.get("status", "HEALTHY")
    logger.info(f"LIA Production Startup Complete. Status: {status_code}")
    return {
        "success": True,
        "status": status_code,
        "missing_config": missing,
        "health": health_status
    }


@llm.function_tool(
    name="configure_desktop_startup",
    description="Enable or disable LIA Windows Desktop auto-startup on boot.",
)
async def configure_desktop_startup(enable: bool = True) -> str:
    logger.info(f"[LIA STARTUP TOOL TRIGGERED] configure_desktop_startup(enable={enable})")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_configure_startup, enable)
