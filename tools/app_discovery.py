"""
Dynamic Application Discovery Engine for LIA (JARVIS Computer Control Master)
Safely discovers installed Windows applications using Start Menu shortcuts,
App Paths in Registry, system binaries, and UWP app protocols.
"""

import os
import sys
import glob
import time
import logging
from typing import Dict, Any, List, Optional

if sys.platform == "win32":
    import winreg
else:
    winreg = None

logger = logging.getLogger("lia-app-discovery")

# Known system executables mapping normalized names to system commands
SYSTEM_APP_MAP: Dict[str, Dict[str, str]] = {
    "chrome": {"display_name": "Google Chrome", "cmd": "chrome.exe", "publisher": "Google LLC"},
    "google chrome": {"display_name": "Google Chrome", "cmd": "chrome.exe", "publisher": "Google LLC"},
    "edge": {"display_name": "Microsoft Edge", "cmd": "msedge.exe", "publisher": "Microsoft Corporation"},
    "microsoft edge": {"display_name": "Microsoft Edge", "cmd": "msedge.exe", "publisher": "Microsoft Corporation"},
    "firefox": {"display_name": "Mozilla Firefox", "cmd": "firefox.exe", "publisher": "Mozilla"},
    "vs code": {"display_name": "Visual Studio Code", "cmd": "code.cmd", "publisher": "Microsoft Corporation"},
    "vscode": {"display_name": "Visual Studio Code", "cmd": "code.cmd", "publisher": "Microsoft Corporation"},
    "code": {"display_name": "Visual Studio Code", "cmd": "code.cmd", "publisher": "Microsoft Corporation"},
    "notepad": {"display_name": "Notepad", "cmd": "notepad.exe", "publisher": "Microsoft Corporation"},
    "calculator": {"display_name": "Calculator", "cmd": "calc.exe", "publisher": "Microsoft Corporation"},
    "calc": {"display_name": "Calculator", "cmd": "calc.exe", "publisher": "Microsoft Corporation"},
    "file explorer": {"display_name": "File Explorer", "cmd": "explorer.exe", "publisher": "Microsoft Corporation"},
    "explorer": {"display_name": "File Explorer", "cmd": "explorer.exe", "publisher": "Microsoft Corporation"},
    "cmd": {"display_name": "Command Prompt", "cmd": "cmd.exe", "publisher": "Microsoft Corporation"},
    "command prompt": {"display_name": "Command Prompt", "cmd": "cmd.exe", "publisher": "Microsoft Corporation"},
    "terminal": {"display_name": "Windows Terminal", "cmd": "wt.exe", "publisher": "Microsoft Corporation"},
    "powershell": {"display_name": "Windows PowerShell", "cmd": "powershell.exe", "publisher": "Microsoft Corporation"},
    "paint": {"display_name": "Paint", "cmd": "mspaint.exe", "publisher": "Microsoft Corporation"},
    "task manager": {"display_name": "Task Manager", "cmd": "taskmgr.exe", "publisher": "Microsoft Corporation"},
    "whatsapp": {"display_name": "WhatsApp", "cmd": "start whatsapp:", "publisher": "Meta Platforms"},
    "facebook": {"display_name": "Facebook", "cmd": "start https://www.facebook.com", "publisher": "Meta Platforms"},
    "instagram": {"display_name": "Instagram", "cmd": "start https://www.instagram.com", "publisher": "Meta Platforms"},
    "twitter": {"display_name": "X (Twitter)", "cmd": "start https://www.x.com", "publisher": "X Corp."},
    "x": {"display_name": "X (Twitter)", "cmd": "start https://www.x.com", "publisher": "X Corp."},
    "youtube": {"display_name": "YouTube", "cmd": "start https://www.youtube.com", "publisher": "Google LLC"},
    "netflix": {"display_name": "Netflix", "cmd": "start https://www.netflix.com", "publisher": "Netflix Inc."},
    "word": {"display_name": "Microsoft Word", "cmd": "winword.exe", "publisher": "Microsoft Corporation"},
    "excel": {"display_name": "Microsoft Excel", "cmd": "excel.exe", "publisher": "Microsoft Corporation"},
    "powerpoint": {"display_name": "Microsoft PowerPoint", "cmd": "powerpnt.exe", "publisher": "Microsoft Corporation"},
    "outlook": {"display_name": "Microsoft Outlook", "cmd": "outlook.exe", "publisher": "Microsoft Corporation"},
    "spotify": {"display_name": "Spotify", "cmd": "start spotify:", "publisher": "Spotify AB"},
    "discord": {"display_name": "Discord", "cmd": "Update.exe --processStart Discord.exe", "publisher": "Discord Inc."},
    "telegram": {"display_name": "Telegram", "cmd": "Telegram.exe", "publisher": "Telegram FZ-LLC"},
    "teams": {"display_name": "Microsoft Teams", "cmd": "ms-teams.exe", "publisher": "Microsoft Corporation"},
    "zoom": {"display_name": "Zoom", "cmd": "Zoom.exe", "publisher": "Zoom Video Communications"},
    "slack": {"display_name": "Slack", "cmd": "slack.exe", "publisher": "Slack Technologies"},
    "vlc": {"display_name": "VLC Media Player", "cmd": "vlc.exe", "publisher": "VideoLAN"},
}


class ApplicationDiscoveryManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ApplicationDiscoveryManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._last_scan_time: float = 0.0
        self.discover_installed_applications()

    def is_safe_launch_target(self, target: str) -> bool:
        """Validates launch target string to prevent dangerous command injections."""
        if not target or not isinstance(target, str):
            return False
        t_clean = target.strip().lower()

        # Reject dangerous shell operators / chaining
        dangerous_tokens = ["&", "|", ";", "`", "$", "rm ", "del /", "format ", "powershell -enc", "drop database"]
        for token in dangerous_tokens:
            if token in t_clean:
                return False

        # Allow valid executables, .lnk files, or safe URI protocols
        if any(t_clean.endswith(ext) for ext in [".exe", ".cmd", ".bat", ".lnk"]):
            return True
        if any(t_clean.startswith(prefix) for prefix in ["start ", "ms-", "whatsapp:", "spotify:"]):
            return True
        if t_clean in SYSTEM_APP_MAP or any(target.endswith(app_name) for app_name in SYSTEM_APP_MAP):
            return True

        return True

    def scan_start_menu(self) -> List[Dict[str, Any]]:
        """Scans Windows Start Menu shortcuts (.lnk files) for installed applications."""
        discovered = []
        if sys.platform != "win32":
            return discovered
        start_menu_dirs = [
            r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
            os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs")
        ]

        for d in start_menu_dirs:
            if not os.path.exists(d):
                continue
            try:
                for root, _, files in os.walk(d):
                    for file in files:
                        if file.lower().endswith(".lnk"):
                            app_name = os.path.splitext(file)[0]
                            norm_key = app_name.lower().strip()
                            lnk_path = os.path.join(root, file)

                            discovered.append({
                                "application_name": norm_key,
                                "display_name": app_name,
                                "launch_identifier": lnk_path,
                                "installation_path": lnk_path,
                                "publisher": "Windows Start Menu",
                                "availability": "AVAILABLE",
                                "last_verified_time": time.time()
                            })
            except Exception as err:
                logger.warning(f"Error scanning Start Menu directory '{d}': {err}")

        return discovered

    def scan_registry_app_paths(self) -> List[Dict[str, Any]]:
        """Scans Windows Registry HKLM/HKCU App Paths for registered executables."""
        discovered = []
        if sys.platform != "win32":
            return discovered

        registry_keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths")
        ]

        for hkey, subkey_path in registry_keys:
            try:
                with winreg.OpenKey(hkey, subkey_path) as key:
                    num_subkeys, _, _ = winreg.QueryInfoKey(key)
                    for i in range(num_subkeys):
                        try:
                            exe_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, exe_name) as app_key:
                                try:
                                    path_val, _ = winreg.QueryValueEx(app_key, "")
                                    app_title = os.path.splitext(exe_name)[0]
                                    discovered.append({
                                        "application_name": app_title.lower().strip(),
                                        "display_name": app_title.title(),
                                        "launch_identifier": path_val or exe_name,
                                        "installation_path": path_val or exe_name,
                                        "publisher": "Registry App Paths",
                                        "availability": "AVAILABLE",
                                        "last_verified_time": time.time()
                                    })
                                except Exception:
                                    pass
                        except Exception:
                            continue
            except Exception:
                continue

        return discovered

    def discover_installed_applications(self, force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """Populates and returns the complete application registry."""
        now = time.time()
        if not force_refresh and (now - self._last_scan_time < 300) and self._registry:
            return self._registry

        registry: Dict[str, Dict[str, Any]] = {}

        # 1. Populate standard system app map
        for key, info in SYSTEM_APP_MAP.items():
            registry[key] = {
                "application_name": key,
                "display_name": info["display_name"],
                "launch_identifier": info["cmd"],
                "installation_path": info["cmd"],
                "publisher": info["publisher"],
                "availability": "AVAILABLE",
                "last_verified_time": now
            }

        # 2. Add Registry App Paths
        for item in self.scan_registry_app_paths():
            k = item["application_name"]
            if k not in registry:
                registry[k] = item

        # 3. Add Start Menu shortcuts
        for item in self.scan_start_menu():
            k = item["application_name"]
            if k not in registry:
                registry[k] = item

        self._registry = registry
        self._last_scan_time = now
        logger.info(f"Discovered {len(registry)} installed application entries.")
        return self._registry

    def find_application(self, query: str) -> Optional[Dict[str, Any]]:
        """Finds best matching discovered application for natural language query."""
        if not query:
            return None
        q_norm = query.strip().lower()

        apps = self.discover_installed_applications()

        # Exact match
        if q_norm in apps:
            return apps[q_norm]

        # Partial match
        for key, entry in apps.items():
            if key in q_norm or q_norm in key or entry["display_name"].lower() in q_norm:
                return entry

        return None


_global_app_discovery: Optional[ApplicationDiscoveryManager] = None


def get_app_discovery_manager() -> ApplicationDiscoveryManager:
    global _global_app_discovery
    if _global_app_discovery is None:
        _global_app_discovery = ApplicationDiscoveryManager()
    return _global_app_discovery
