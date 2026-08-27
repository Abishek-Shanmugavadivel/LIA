"""
Windows Desktop Control & Application Registry Tools for LIA 5.0

Cross-platform safe version:
- Windows: full desktop/application/window control.
- Linux/macOS: module can be imported safely, but Windows-specific
  desktop/window operations are disabled.
- Prevents Render/Linux deployment from crashing because of pygetwindow.
"""

import os
import sys
import subprocess
import logging
import asyncio
import platform
import psutil

from typing import Dict, List

from livekit.agents import llm


logger = logging.getLogger("lia-tools-desktop")


# =========================================================
# PLATFORM DETECTION
# =========================================================

IS_WINDOWS = platform.system().lower() == "windows"

# pygetwindow is Windows-specific in this project.
# IMPORTANT:
# Do NOT import it on Linux/Render.
if IS_WINDOWS:
    try:
        import pygetwindow as gw
    except ImportError:
        gw = None
        logger.warning(
            "pygetwindow is not installed. Windows window-management "
            "features will be unavailable."
        )
else:
    gw = None
    logger.info(
        "Non-Windows platform detected (%s). "
        "Windows desktop window-management features disabled.",
        platform.system(),
    )


# =========================================================
# CONTROLLED APPLICATION ALLOWLIST
# =========================================================

APPLICATION_ALLOWLIST: Dict[str, List[str]] = {
    "chrome": [
        "chrome.exe",
        "start chrome",
    ],
    "google chrome": [
        "chrome.exe",
        "start chrome",
    ],
    "google": [
        "start https://www.google.com",
        "chrome.exe",
    ],
    "vs code": [
        "code.cmd",
        "code.exe",
        "code",
    ],
    "vscode": [
        "code.cmd",
        "code.exe",
        "code",
    ],
    "code": [
        "code.cmd",
        "code.exe",
        "code",
    ],
    "notepad": [
        "notepad.exe",
    ],
    "calculator": [
        "calc.exe",
    ],
    "calc": [
        "calc.exe",
    ],
    "file explorer": [
        "explorer.exe",
    ],
    "explorer": [
        "explorer.exe",
    ],
    "whatsapp": [
        "WhatsApp.exe",
        "start whatsapp:",
        "start https://web.whatsapp.com",
    ],
    "whatsapp web": [
        "start https://web.whatsapp.com",
    ],
    "youtube": [
        "start https://www.youtube.com",
    ],
    "spotify": [
        "Spotify.exe",
        "start spotify:",
        "start https://open.spotify.com",
    ],
    "gmail": [
        "start https://mail.google.com",
    ],
    "mail": [
        "start ms-outlook:",
        "start https://mail.google.com",
    ],
    "settings": [
        "start ms-settings:",
    ],
    "terminal": [
        "wt.exe",
        "cmd.exe",
    ],
    "windows terminal": [
        "wt.exe",
        "cmd.exe",
    ],
    "cmd": [
        "cmd.exe",
    ],
    "command prompt": [
        "cmd.exe",
    ],
    "powershell": [
        "powershell.exe",
    ],
    "edge": [
        "msedge.exe",
    ],
    "microsoft edge": [
        "msedge.exe",
    ],
    "paint": [
        "mspaint.exe",
    ],
    "mspaint": [
        "mspaint.exe",
    ],
    "task manager": [
        "taskmgr.exe",
    ],
    "taskmgr": [
        "taskmgr.exe",
    ],
}


# =========================================================
# CONTROLLED PROCESS CLOSE ALLOWLIST
# =========================================================

PROCESS_CLOSE_ALLOWLIST: Dict[str, List[str]] = {
    "chrome": [
        "chrome.exe",
    ],
    "google chrome": [
        "chrome.exe",
    ],
    "notepad": [
        "notepad.exe",
    ],
    "calculator": [
        "calc.exe",
        "CalculatorApp.exe",
    ],
    "calc": [
        "calc.exe",
        "CalculatorApp.exe",
    ],
    "vs code": [
        "code.exe",
    ],
    "vscode": [
        "code.exe",
    ],
    "code": [
        "code.exe",
    ],
    "whatsapp": [
        "WhatsApp.exe",
    ],
    "spotify": [
        "Spotify.exe",
    ],
    "edge": [
        "msedge.exe",
    ],
    "paint": [
        "mspaint.exe",
    ],
    "cmd": [
        "cmd.exe",
    ],
}


# =========================================================
# CONTROLLED FOLDER ALLOWLIST
# =========================================================

FOLDER_ALLOWLIST: Dict[str, str] = {
    "downloads": os.path.expanduser("~/Downloads"),
    "documents": os.path.expanduser("~/Documents"),
    "desktop": os.path.expanduser("~/Desktop"),
    "pictures": os.path.expanduser("~/Pictures"),
    "music": os.path.expanduser("~/Music"),
    "videos": os.path.expanduser("~/Videos"),
    "home": os.path.expanduser("~"),
    "profile": os.path.expanduser("~"),
    "temp": (
        os.getenv("TEMP")
        if IS_WINDOWS
        else os.getenv("TMPDIR", "/tmp")
    ),
}


# =========================================================
# PLATFORM GUARD
# =========================================================

def _windows_only_message(feature: str) -> str:
    """Return a consistent message for Windows-only operations."""
    return (
        f"{feature} is only available when LIA is running on Windows. "
        f"Current platform: {platform.system()}."
    )


# =========================================================
# OPEN APPLICATION
# =========================================================

def perform_open_application(app_name: str) -> str:
    """
    Synchronously launch an allowed application.

    Windows:
        Uses Windows application/URI launching.

    Non-Windows:
        Safely refuses Windows desktop application execution.
    """

    normalized = app_name.strip().lower()

    if not normalized:
        return "No application name was provided."

    # -----------------------------------------------------
    # Dynamic Application Discovery
    # -----------------------------------------------------

    try:
        from tools.app_discovery import get_app_discovery_manager

        app_discovery = get_app_discovery_manager()
        discovered_entry = app_discovery.find_application(normalized)

        if (
            discovered_entry
            and app_discovery.is_safe_launch_target(
                discovered_entry["launch_identifier"]
            )
        ):
            cmd = discovered_entry["launch_identifier"]
            display_name = discovered_entry["display_name"]

            logger.info(
                "Opening dynamically discovered application "
                "'%s' (%s)",
                display_name,
                cmd,
            )

            try:
                if IS_WINDOWS:
                    start_cmd = (
                        cmd
                        if (
                            cmd.startswith("start ")
                            or cmd.endswith(".lnk")
                        )
                        else f'start "" "{cmd}"'
                    )

                    subprocess.Popen(
                        start_cmd,
                        shell=True,
                    )

                else:
                    # Linux/macOS backend should not execute arbitrary
                    # desktop applications through this Windows tool.
                    return _windows_only_message(
                        f"Opening '{display_name}'"
                    )

                from tools.tool_result import verify_process_running

                exe_target = (
                    os.path.basename(cmd)
                    if cmd.endswith(".exe")
                    else display_name.lower()
                )

                verified = verify_process_running(
                    [exe_target],
                    max_wait_seconds=1.5,
                )

                if verified:
                    return (
                        f"Successfully opened {display_name} "
                        "(verified active)."
                    )

                return (
                    f"Successfully initiated launch for "
                    f"{display_name}."
                )

            except Exception as err:
                logger.warning(
                    "Dynamic launch failed for '%s': %s",
                    cmd,
                    err,
                )

    except Exception as err:
        logger.debug(
            "Dynamic application discovery unavailable: %s",
            err,
        )

    # -----------------------------------------------------
    # Static Allowlist
    # -----------------------------------------------------

    matched_key = None

    for key in APPLICATION_ALLOWLIST:
        if key in normalized or normalized in key:
            matched_key = key
            break

    if not matched_key:
        allowed_list_str = ", ".join(
            list(APPLICATION_ALLOWLIST.keys())[:10]
        )

        return (
            f"Application '{app_name}' is not in the "
            f"controlled application registry. "
            f"Supported applications include: "
            f"{allowed_list_str}."
        )

    # -----------------------------------------------------
    # Prevent Windows commands from running on Render/Linux
    # -----------------------------------------------------

    if not IS_WINDOWS:
        return _windows_only_message(
            f"Opening '{matched_key.title()}'"
        )

    logger.info(
        "Opening application '%s' requested by user",
        matched_key,
    )

    exec_cmds = APPLICATION_ALLOWLIST[matched_key]

    for cmd in exec_cmds:
        try:
            if IS_WINDOWS:
                if cmd.startswith("start "):
                    start_cmd = cmd
                else:
                    start_cmd = f"start {cmd}"

                subprocess.Popen(
                    start_cmd,
                    shell=True,
                )
            else:
                return _windows_only_message(
                    f"Opening '{matched_key.title()}'"
                )

            # -------------------------------------------------
            # Action Verification
            # -------------------------------------------------

            from tools.tool_result import verify_process_running

            exes = [
                c
                for c in exec_cmds
                if c.endswith(".exe")
            ]

            verified = (
                verify_process_running(
                    exes,
                    max_wait_seconds=1.5,
                )
                if exes
                else True
            )

            display_name = (
                "WhatsApp"
                if "whatsapp" in matched_key
                else matched_key.title()
            )

            if verified:
                return (
                    f"Successfully opened {display_name} "
                    "(verified active)."
                )

            return (
                f"Successfully initiated launch for "
                f"{display_name}."
            )

        except Exception as e:
            logger.warning(
                "Failed to open '%s': %s",
                cmd,
                e,
            )

    return (
        f"Could not launch '{app_name}' because it was "
        f"not found on this system."
    )


# =========================================================
# CLOSE APPLICATION
# =========================================================

def perform_close_application(app_name: str) -> str:
    """
    Safely close an allowed application.

    This remains cross-platform because psutil can inspect
    processes on supported platforms, but the allowlist is
    primarily designed for Windows applications.
    """

    normalized = app_name.strip().lower()

    if not normalized:
        return "No application name was provided."

    matched_key = None

    for key in PROCESS_CLOSE_ALLOWLIST:
        if key in normalized or normalized in key:
            matched_key = key
            break

    if not matched_key:
        return (
            f"Closing application '{app_name}' is not "
            f"permitted or supported."
        )

    # Desktop application process names in this allowlist
    # are Windows-specific.
    if not IS_WINDOWS:
        return _windows_only_message(
            f"Closing '{matched_key.title()}'"
        )

    target_exes = PROCESS_CLOSE_ALLOWLIST[matched_key]

    logger.info(
        "Closing application '%s' matching executables: %s",
        app_name,
        target_exes,
    )

    closed_count = 0

    try:
        for proc in psutil.process_iter(
            ["pid", "name"]
        ):
            try:
                proc_name = proc.info["name"]

                if proc_name and any(
                    target_exe.lower() in proc_name.lower()
                    or normalized in proc_name.lower()
                    for target_exe in target_exes
                ):
                    proc.terminate()
                    closed_count += 1

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess,
            ):
                continue

    except Exception as err:
        logger.error(
            "Error terminating process for '%s': %s",
            app_name,
            err,
        )

        return (
            f"Error occurred while closing "
            f"{app_name}: {err}"
        )

    app_disp = (
        matched_key.title()
        if matched_key
        else app_name.title()
    )

    if closed_count > 0:
        return (
            f"Successfully closed {app_disp} "
            f"({closed_count} process instance(s) terminated)."
        )

    return f"{app_disp} is not currently running."


# =========================================================
# OPEN FOLDER
# =========================================================

def perform_open_folder(folder_name: str) -> str:
    """
    Open an allowed user folder.

    Windows:
        Uses File Explorer.

    Linux:
        Uses xdg-open where available.

    macOS:
        Uses open.
    """

    normalized = folder_name.strip().lower()

    if not normalized:
        return "No folder name was provided."

    matched_key = None

    for key in FOLDER_ALLOWLIST:
        if key in normalized or normalized in key:
            matched_key = key
            break

    if not matched_key:
        allowed_folders = ", ".join(
            FOLDER_ALLOWLIST.keys()
        )

        return (
            f"Folder '{folder_name}' is not in the "
            f"safe folder allowlist "
            f"({allowed_folders})."
        )

    target_path = os.path.abspath(
        FOLDER_ALLOWLIST[matched_key]
    )

    if not os.path.exists(target_path):
        return (
            f"Folder path '{target_path}' does not "
            f"exist on this system."
        )

    try:
        if IS_WINDOWS:
            os.startfile(target_path)

        elif sys.platform == "darwin":
            subprocess.Popen(
                ["open", target_path]
            )

        else:
            subprocess.Popen(
                ["xdg-open", target_path]
            )

        return (
            f"Opened {matched_key.title()} folder."
        )

    except Exception as e:
        logger.error(
            "Error opening folder '%s': %s",
            target_path,
            e,
        )

        return (
            f"Could not open {matched_key.title()} "
            f"folder: {str(e)}"
        )


# =========================================================
# WINDOW MANAGEMENT
# =========================================================

def perform_window_state(
    window_title: str,
    action: str = "minimize",
) -> str:
    """
    Minimize, maximize, restore, or activate a window.

    This feature is Windows-only because pygetwindow is
    intentionally not imported on Linux/macOS.
    """

    if not IS_WINDOWS or gw is None:
        return _windows_only_message(
            "Window management"
        )

    action_clean = action.strip().lower()
    title_clean = window_title.strip().lower()

    if not window_title.strip():
        return "No window title was provided."

    try:
        windows = gw.getWindowsWithTitle(
            window_title
        )

        if not windows:
            all_wins = gw.getAllWindows()

            windows = [
                w
                for w in all_wins
                if title_clean in w.title.lower()
                and w.title.strip()
            ]

    except Exception as e:
        logger.error(
            "Unable to inspect windows: %s",
            e,
        )

        return (
            f"Could not inspect desktop windows: {e}"
        )

    if not windows:
        return (
            f"No open window matching "
            f"'{window_title}' was found."
        )

    win = windows[0]

    try:
        if action_clean == "minimize":
            win.minimize()

            return (
                f"Minimized window '{win.title}'."
            )

        if action_clean == "maximize":
            win.maximize()

            return (
                f"Maximized window '{win.title}'."
            )

        if action_clean in [
            "restore",
            "unminimize",
        ]:
            win.restore()

            return (
                f"Restored window '{win.title}'."
            )

        if action_clean in [
            "switch",
            "activate",
            "focus",
        ]:
            win.activate()

            return (
                f"Switched focus to window "
                f"'{win.title}'."
            )

        return (
            f"Unknown window action '{action}'. "
            f"Supported: minimize, maximize, "
            f"restore, switch."
        )

    except Exception as e:
        logger.error(
            "Window action failed: %s",
            e,
        )

        return (
            f"Could not perform {action} on window "
            f"'{window_title}': {e}"
        )


# =========================================================
# LIVEKIT FUNCTION TOOLS
# =========================================================

@llm.function_tool(
    name="open_application",
    description=(
        "Open a desktop application from LIA's "
        "controlled registry such as Chrome, WhatsApp, "
        "Spotify, YouTube, VS Code, Notepad, Calculator, "
        "Gmail, Settings, or Terminal."
    ),
)
async def open_application(
    app_name: str,
) -> str:

    logger.info(
        "[LIA DESKTOP TOOL TRIGGERED] "
        "open_application('%s')",
        app_name,
    )

    loop = asyncio.get_event_loop()

    return await loop.run_in_executor(
        None,
        perform_open_application,
        app_name,
    )


@llm.function_tool(
    name="close_application",
    description=(
        "Close an allowed desktop application on "
        "Windows such as Chrome, WhatsApp, Spotify, "
        "Notepad, Calculator, VS Code, etc."
    ),
)
async def close_application(
    app_name: str,
) -> str:

    logger.info(
        "[LIA DESKTOP TOOL TRIGGERED] "
        "close_application('%s')",
        app_name,
    )

    loop = asyncio.get_event_loop()

    return await loop.run_in_executor(
        None,
        perform_close_application,
        app_name,
    )


@llm.function_tool(
    name="open_folder",
    description=(
        "Open a safe system folder such as Downloads, "
        "Documents, Desktop, Pictures, Music, or Videos."
    ),
)
async def open_folder(
    folder_name: str,
) -> str:

    logger.info(
        "[LIA DESKTOP TOOL TRIGGERED] "
        "open_folder('%s')",
        folder_name,
    )

    loop = asyncio.get_event_loop()

    return await loop.run_in_executor(
        None,
        perform_open_folder,
        folder_name,
    )


@llm.function_tool(
    name="manage_window",
    description=(
        "Minimize, maximize, restore, or switch focus "
        "to an open desktop window such as Chrome, "
        "VS Code, or WhatsApp."
    ),
)
async def manage_window(
    window_title: str,
    action: str = "minimize",
) -> str:

    logger.info(
        "[LIA DESKTOP TOOL TRIGGERED] "
        "manage_window('%s', '%s')",
        window_title,
        action,
    )

    loop = asyncio.get_event_loop()

    return await loop.run_in_executor(
        None,
        perform_window_state,
        window_title,
        action,
    )