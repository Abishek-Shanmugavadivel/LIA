"""
Music & Media Control Tools for LIA (Phases 4-8 Expanded)
Supports playing music on YouTube/Spotify, searching song titles, and controlling playback
(play, pause, resume, next, previous, volume up, volume down, mute).
"""

import logging
import urllib.parse
import sys
import os
import asyncio
import pyautogui
from livekit.agents import llm

logger = logging.getLogger("lia-tools-media")
pyautogui.FAILSAFE = False


def perform_play_music(query: str = None, platform: str = "youtube") -> str:
    """Synchronous helper to play music or search songs on YouTube/Spotify."""
    plat_clean = platform.strip().lower() if platform else "youtube"
    
    if not query:
        # Open main platform player
        if plat_clean == "spotify":
            url = "https://open.spotify.com"
        else:
            url = "https://www.youtube.com"
        if sys.platform == "win32":
            os.system(f"start {url}")
        return f"Opened {plat_clean.title()} player."

    encoded_query = urllib.parse.quote(query)
    if plat_clean == "spotify":
        url = f"https://open.spotify.com/search/{encoded_query}"
        desc = f"Searching and playing '{query}' on Spotify."
    else:
        url = f"https://www.youtube.com/results?search_query={encoded_query}"
        desc = f"Searching and playing '{query}' on YouTube."

    logger.info(f"Playing media on {plat_clean}: '{query}' -> {url}")
    try:
        if sys.platform == "win32":
            os.system(f"start {url}")
        return desc
    except Exception as e:
        logger.error(f"Error launching media player URL: {e}")
        return f"Could not open {plat_clean}: {e}"


def perform_control_media(action: str) -> str:
    """Synchronous helper for media key commands (play, pause, next, volume up/down, mute)."""
    act = action.strip().lower()
    
    try:
        if act in ["play", "pause", "resume", "stop", "toggle"]:
            pyautogui.press("playpause")
            return "Toggled media playback (Play/Pause)."
        elif act in ["next", "skip", "next song", "next track"]:
            pyautogui.press("nexttrack")
            return "Skipped to next track."
        elif act in ["previous", "prev", "back", "previous song"]:
            pyautogui.press("prevtrack")
            return "Returned to previous track."
        elif act in ["volume_up", "volume up", "louder", "increase volume"]:
            for _ in range(5):
                pyautogui.press("volumeup")
            return "Increased media volume."
        elif act in ["volume_down", "volume down", "quieter", "decrease volume"]:
            for _ in range(5):
                pyautogui.press("volumedown")
            return "Decreased media volume."
        elif act in ["mute", "unmute", "toggle mute"]:
            pyautogui.press("volumemute")
            return "Toggled audio mute."
        else:
            return f"Unknown media action '{action}'. Supported: play, pause, next, previous, volume up, volume down, mute."
    except Exception as e:
        logger.error(f"Error executing media action '{action}': {e}")
        return f"Could not perform media action '{action}': {e}"


@llm.function_tool(
    name="play_music",
    description="Play songs, artists, or playlists on YouTube or Spotify (e.g. 'play Tamil songs', 'play synthwave on Spotify').",
)
async def play_music(query: str = None, platform: str = "youtube") -> str:
    logger.info(f"[LIA MEDIA TOOL TRIGGERED] play_music(query='{query}', platform='{platform}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_play_music, query, platform)


@llm.function_tool(
    name="control_media",
    description="Control active media playback: play, pause, resume, next, previous, volume up, volume down, or mute.",
)
async def control_media(action: str) -> str:
    logger.info(f"[LIA MEDIA TOOL TRIGGERED] control_media(action='{action}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_control_media, action)
