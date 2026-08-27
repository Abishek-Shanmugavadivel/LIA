"""
JARVIS Operating Modes Controller for LIA (Phase 9)
Modes:
- Study Mode: Launches documentation, study tabs, notes/PDF apps, quiet background.
- Coding Mode: Launches VS Code, Chrome dev tabs, API documentation, project folder.
- Work Mode: Launches Email client, Slack/Teams, Calendar, work documents.
- Entertainment Mode: Launches YouTube/Music player, Discord, games launcher.
"""

import os
import sys
import logging
import asyncio
from typing import Dict, Any, List
from livekit.agents import llm
from tools.desktop import open_application, open_folder
from tools.browser import open_website
from tools.media import play_music

logger = logging.getLogger("lia-modes")

MODE_CONFIGS: Dict[str, Dict[str, Any]] = {
    "coding": {
        "name": "Coding Mode",
        "apps": ["vscode"],
        "folders": ["Projects"],
        "urls": ["https://github.com", "https://stackoverflow.com", "https://docs.python.org"],
        "description": "Opens VS Code, GitHub, Stack Overflow, and Projects folder.",
        "status_message": "🚀 Coding Mode active. Environment initialized with VS Code, Dev Tabs & Project Workspace."
    },
    "study": {
        "name": "Study Mode",
        "apps": ["notepad"],
        "folders": ["Documents"],
        "urls": ["https://wikipedia.org", "https://scholar.google.com"],
        "description": "Opens Notepad, Documents folder, and research tools.",
        "status_message": "📚 Study Mode active. Open for research, notes, and focused learning."
    },
    "work": {
        "name": "Work Mode",
        "apps": ["calc"],
        "folders": ["Documents"],
        "urls": ["https://mail.google.com", "https://calendar.google.com"],
        "description": "Opens Email, Calendar, Calculator, and Documents.",
        "status_message": "💼 Work Mode active. Productivity suite ready."
    },
    "entertainment": {
        "name": "Entertainment Mode",
        "apps": [],
        "folders": ["Downloads"],
        "urls": ["https://www.youtube.com", "https://open.spotify.com"],
        "description": "Opens YouTube and Spotify music player.",
        "status_message": "🎮 Entertainment Mode active. Media player and music channels ready."
    }
}

active_mode = "default"

def get_active_mode() -> str:
    global active_mode
    return active_mode

def perform_activate_jarvis_mode(mode_name: str) -> str:
    """Synchronous helper to execute application & browser cluster launching for a JARVIS Mode."""
    global active_mode
    m_clean = mode_name.strip().lower()
    
    # Map synonyms
    if "code" in m_clean or "developer" in m_clean or "coding" in m_clean:
        target_key = "coding"
    elif "study" in m_clean or "learn" in m_clean or "research" in m_clean:
        target_key = "study"
    elif "work" in m_clean or "office" in m_clean or "productivity" in m_clean:
        target_key = "work"
    elif "entertainment" in m_clean or "game" in m_clean or "fun" in m_clean or "music" in m_clean:
        target_key = "entertainment"
    else:
        target_key = "coding"

    config = MODE_CONFIGS[target_key]
    active_mode = config["name"]

    logger.info(f"Activating JARVIS Mode: {config['name']}")

    # Launch applications
    for app in config["apps"]:
        try:
            asyncio.run(open_application(app))
        except Exception as e:
            logger.warning(f"Could not launch app '{app}': {e}")

    # Launch folders
    for folder in config["folders"]:
        try:
            asyncio.run(open_folder(folder))
        except Exception as e:
            logger.warning(f"Could not open folder '{folder}': {e}")

    # Launch websites
    for url in config["urls"]:
        try:
            asyncio.run(open_website(url))
        except Exception as e:
            logger.warning(f"Could not open website '{url}': {e}")

    return config["status_message"]


@llm.function_tool(
    name="activate_jarvis_mode",
    description="Activate a JARVIS Mode (e.g. 'Start coding mode', 'Study mode', 'Work mode', 'Entertainment mode'). Launches workspace tools.",
)
async def activate_jarvis_mode(mode_name: str) -> str:
    logger.info(f"[LIA MODE TOOL TRIGGERED] activate_jarvis_mode(mode_name='{mode_name}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_activate_jarvis_mode, mode_name)
