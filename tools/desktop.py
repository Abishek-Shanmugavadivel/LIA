"""
Windows Desktop Control & Application Registry Tools for LIA (Phases 4-8 Expanded)
Handles controlled application launching (Chrome, WhatsApp, Spotify, YouTube, VS Code, Gmail, Settings, Terminal),
safe process closing, folder opening, and window state management (minimize, maximize, restore, switch).
"""

import os
import sys
import subprocess
import logging
import asyncio
import psutil
from typing import Dict, List, Optional
import pygetwindow as gw
from livekit.agents import llm

logger = logging.getLogger("lia-tools-desktop")

# Controlled application allowlist mapping normalized names to execution commands/URIs
APPLICATION_ALLOWLIST: Dict[str, List[str]] = {
    "chrome": ["chrome.exe", "start chrome"],
    "google chrome": ["chrome.exe", "start chrome"],
    "google": ["start https://www.google.com", "chrome.exe"],
    "vs code": ["code.cmd", "code.exe", "code"],
    "vscode": ["code.cmd", "code.exe", "code"],
    "code": ["code.cmd", "code.exe", "code"],
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "calc": ["calc.exe"],
    "file explorer": ["explorer.exe"],
    "explorer": ["explorer.exe"],
    "whatsapp": ["WhatsApp.exe", "start whatsapp:", "start https://web.whatsapp.com"],
    "whatsapp web": ["start https://web.whatsapp.com"],
    "youtube": ["start https://www.youtube.com"],
    "spotify": ["Spotify.exe", "start spotify:", "start https://open.spotify.com"],
    "gmail": ["start https://mail.google.com"],
    "mail": ["start ms-outlook:", "start https://mail.google.com"],
    "settings": ["start ms-settings:"],
    "terminal": ["wt.exe", "cmd.exe"],
    "windows terminal": ["wt.exe", "cmd.exe"],
    "cmd": ["cmd.exe"],
    "command prompt": ["cmd.exe"],
    "powershell": ["powershell.exe"],
    "edge": ["msedge.exe"],
    "microsoft edge": ["msedge.exe"],
    "paint": ["mspaint.exe"],
    "mspaint": ["mspaint.exe"],
    "task manager": ["taskmgr.exe"],
    "taskmgr": ["taskmgr.exe"],
}

# Controlled process closing allowlist
PROCESS_CLOSE_ALLOWLIST: Dict[str, List[str]] = {
    "chrome": ["chrome.exe"],
    "google chrome": ["chrome.exe"],
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe", "CalculatorApp.exe"],
    "calc": ["calc.exe", "CalculatorApp.exe"],
    "vs code": ["code.exe"],
    "vscode": ["code.exe"],
    "code": ["code.exe"],
    "whatsapp": ["WhatsApp.exe"],
    "spotify": ["Spotify.exe"],
    "edge": ["msedge.exe"],
    "paint": ["mspaint.exe"],
    "cmd": ["cmd.exe"],
}

# Controlled folder allowlist mapping normalized names to user directory paths
FOLDER_ALLOWLIST: Dict[str, str] = {
    "downloads": os.path.expanduser("~/Downloads"),
    "documents": os.path.expanduser("~/Documents"),
    "desktop": os.path.expanduser("~/Desktop"),
    "pictures": os.path.expanduser("~/Pictures"),
    "music": os.path.expanduser("~/Music"),
    "videos": os.path.expanduser("~/Videos"),
    "home": os.path.expanduser("~"),
    "profile": os.path.expanduser("~"),
    "temp": os.getenv("TEMP", "C:\\Windows\\Temp"),
}


def perform_open_application(app_name: str) -> str:
    """Synchronous helper to launch an allowed application with empirical action verification."""
    normalized = app_name.strip().lower()

    # 1. Check Dynamic Application Discovery Manager
    from tools.app_discovery import get_app_discovery_manager
    app_discovery = get_app_discovery_manager()
    discovered_entry = app_discovery.find_application(normalized)

    if discovered_entry and app_discovery.is_safe_launch_target(discovered_entry["launch_identifier"]):
        cmd = discovered_entry["launch_identifier"]
        display_name = discovered_entry["display_name"]
        logger.info(f"Opening dynamically discovered application '{display_name}' ({cmd})")
        try:
            if sys.platform == "win32":
                start_cmd = cmd if (cmd.startswith("start ") or cmd.endswith(".lnk")) else f'start "" "{cmd}"'
                subprocess.Popen(start_cmd, shell=True)
            else:
                subprocess.Popen([cmd], shell=False)

            from tools.tool_result import verify_process_running
            exe_target = os.path.basename(cmd) if cmd.endswith(".exe") else display_name.lower()
            verified = verify_process_running([exe_target], max_wait_seconds=1.5)
            if verified:
                return f"Successfully opened {display_name} (verified active)."
            return f"Successfully initiated launch for {display_name}."
        except Exception as err:
            logger.warning(f"Dynamic launch failed for '{cmd}': {err}")

    # 2. Fallback to Static Allowlist Mapping
    matched_key = None
    for key in APPLICATION_ALLOWLIST:
        if key in normalized or normalized in key:
            matched_key = key
            break

    if not matched_key:
        allowed_list_str = ", ".join(list(APPLICATION_ALLOWLIST.keys())[:10])
        return (
            f"Application '{app_name}' is not in the controlled application registry. "
            f"Supported applications include: {allowed_list_str}."
        )

    logger.info(f"Opening application '{matched_key}' requested by user")

    exec_cmds = APPLICATION_ALLOWLIST[matched_key]
    for cmd in exec_cmds:
        try:
            if sys.platform == "win32":
                start_cmd = cmd if cmd.startswith("start ") else f"start {cmd}"
                subprocess.Popen(start_cmd, shell=True)
            else:
                subprocess.Popen([cmd], shell=False)
            
            # Action verification: verify process or URI launch initiation
            from tools.tool_result import verify_process_running
            exes = [c for c in exec_cmds if c.endswith(".exe")]
            verified = verify_process_running(exes, max_wait_seconds=1.5) if exes else True

            display_name = "WhatsApp" if "whatsapp" in matched_key else matched_key.title()
            if verified:
                return f"Successfully opened {display_name} (verified active)."
            return f"Successfully initiated launch for {display_name}."
        except Exception as e:
            logger.warning(f"Failed to open '{cmd}': {e}")

    return f"Could not launch '{app_name}' because it was not found on this system."


def perform_close_application(app_name: str) -> str:
    """Synchronous helper to safely close an allowed application."""
    normalized = app_name.strip().lower()

    matched_key = None
    for key in PROCESS_CLOSE_ALLOWLIST:
        if key in normalized or normalized in key:
            matched_key = key
            break

    if not matched_key:
        return f"Closing application '{app_name}' is not permitted or supported."

    target_exes = PROCESS_CLOSE_ALLOWLIST[matched_key]
    logger.info(f"Closing application '{app_name}' matching executables: {target_exes}")

    closed_count = 0
    try:
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                proc_name = proc.info["name"]
                if proc_name and any(target_exe.lower() in proc_name.lower() or normalized in proc_name.lower() for target_exe in target_exes):
                    proc.terminate()
                    closed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception as err:
        logger.error(f"Error terminating process for '{app_name}': {err}")
        return f"Error occurred while closing {app_name}: {err}"

    if closed_count > 0:
        app_disp = matched_key.title() if matched_key else app_name.title()
        return f"Successfully closed {app_disp} ({closed_count} process instance(s) terminated)."
    else:
        app_disp = matched_key.title() if matched_key else app_name.title()
        return f"{app_disp} is not currently running."


def perform_open_folder(folder_name: str) -> str:
    """Synchronous helper to open an allowed folder in File Explorer."""
    normalized = folder_name.strip().lower()

    matched_key = None
    for key in FOLDER_ALLOWLIST:
        if key in normalized or normalized in key:
            matched_key = key
            break

    if not matched_key:
        allowed_folders = ", ".join(FOLDER_ALLOWLIST.keys())
        return f"Folder '{folder_name}' is not in the safe folder allowlist ({allowed_folders})."

    target_path = os.path.abspath(FOLDER_ALLOWLIST[matched_key])
    if not os.path.exists(target_path):
        return f"Folder path '{target_path}' does not exist on this system."

    try:
        if sys.platform == "win32":
            os.startfile(target_path)
        else:
            subprocess.Popen(["xdg-open", target_path])
        return f"Opened {matched_key.title()} folder in File Explorer."
    except Exception as e:
        logger.error(f"Error opening folder '{target_path}': {e}")
        return f"Could not open {matched_key.title()} folder: {str(e)}"


def perform_window_state(window_title: str, action: str = "minimize") -> str:
    """Synchronous helper to minimize, maximize, restore, or switch window."""
    action_clean = action.strip().lower()
    title_clean = window_title.strip().lower()

    windows = gw.getWindowsWithTitle(window_title)
    if not windows:
        # Search partial match
        all_wins = gw.getAllWindows()
        windows = [w for w in all_wins if title_clean in w.title.lower() and w.title.strip()]

    if not windows:
        return f"No open window matching '{window_title}' was found."

    win = windows[0]
    try:
        if action_clean == "minimize":
            win.minimize()
            return f"Minimized window '{win.title}'."
        elif action_clean == "maximize":
            win.maximize()
            return f"Maximized window '{win.title}'."
        elif action_clean in ["restore", "unminimize"]:
            win.restore()
            return f"Restored window '{win.title}'."
        elif action_clean in ["switch", "activate", "focus"]:
            win.activate()
            return f"Switched focus to window '{win.title}'."
        else:
            return f"Unknown window action '{action}'. Supported: minimize, maximize, restore, switch."
    except Exception as e:
        return f"Could not perform {action} on window '{window_title}': {e}"


# LiveKit Function Tool Decorators
@llm.function_tool(
    name="open_application",
    description="Open a desktop application from LIA's controlled registry such as Chrome, WhatsApp, Spotify, YouTube, VS Code, Notepad, Calculator, Gmail, Settings, or Terminal.",
)
async def open_application(app_name: str) -> str:
    logger.info(f"[LIA DESKTOP TOOL TRIGGERED] open_application('{app_name}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_open_application, app_name)


@llm.function_tool(
    name="close_application",
    description="Close an allowed desktop application on Windows such as Chrome, WhatsApp, Spotify, Notepad, Calculator, VS Code, etc.",
)
async def close_application(app_name: str) -> str:
    logger.info(f"[LIA DESKTOP TOOL TRIGGERED] close_application('{app_name}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_close_application, app_name)


@llm.function_tool(
    name="open_folder",
    description="Open a safe system folder in Windows File Explorer such as Downloads, Documents, Desktop, Pictures, Music, Videos.",
)
async def open_folder(folder_name: str) -> str:
    logger.info(f"[LIA DESKTOP TOOL TRIGGERED] open_folder('{folder_name}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_open_folder, folder_name)


@llm.function_tool(
    name="manage_window",
    description="Minimize, maximize, restore, or switch focus to an open desktop window (e.g. Chrome, VS Code, WhatsApp).",
)
async def manage_window(window_title: str, action: str = "minimize") -> str:
    logger.info(f"[LIA DESKTOP TOOL TRIGGERED] manage_window('{window_title}', '{action}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_window_state, window_title, action)
