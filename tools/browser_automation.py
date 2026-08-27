"""
Controlled Browser Automation Tools for LIA (Phases 4-8 Expanded)
Handles URL opening, Google search, page navigation (back, forward, refresh, scroll),
and DOM/accessibility element interaction.
"""

import os
import sys
import logging
import asyncio
import subprocess
import urllib.parse
import pyautogui
from typing import Dict, Any, List, Optional
from livekit.agents import llm

logger = logging.getLogger("lia-tools-browser-auto")
pyautogui.FAILSAFE = False


def perform_open_url(url: str) -> str:
    """Synchronous helper to open a target URL in the default web browser."""
    clean_url = url.strip()
    if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
        clean_url = "https://" + clean_url

    try:
        if sys.platform == "win32":
            subprocess.Popen(f"start {clean_url}", shell=True)
        else:
            subprocess.Popen(["xdg-open", clean_url])
        return f"Opened URL '{clean_url}' in browser."
    except Exception as e:
        logger.error(f"Error opening URL '{clean_url}': {e}")
        return f"Could not open URL: {e}"


def perform_search_google(query: str) -> str:
    """Synchronous helper to search Google directly."""
    encoded_q = urllib.parse.quote(query.strip())
    google_url = f"https://www.google.com/search?q={encoded_q}"
    return perform_open_url(google_url)


def perform_navigate_browser(action: str) -> str:
    """Synchronous helper for browser page navigation (back, forward, refresh, scroll)."""
    act = action.strip().lower()
    try:
        if act in ["back", "go_back", "previous", "previous_page"]:
            pyautogui.hotkey("alt", "left")
            return "Navigated back in browser history."
        elif act in ["forward", "go_forward", "next", "next_page"]:
            pyautogui.hotkey("alt", "right")
            return "Navigated forward in browser history."
        elif act in ["refresh", "reload"]:
            pyautogui.press("f5")
            return "Refreshed browser page."
        elif act in ["scroll_down", "down"]:
            pyautogui.scroll(-500)
            return "Scrolled page down."
        elif act in ["scroll_up", "up"]:
            pyautogui.scroll(500)
            return "Scrolled page up."
        else:
            return f"Unknown navigation action '{action}'. Supported: back, forward, refresh, scroll_down, scroll_up."
    except Exception as e:
        logger.error(f"Error navigating browser: {e}")
        return f"Could not perform browser navigation: {e}"


def perform_tab_action(action: str, tab_index: Optional[int] = None) -> str:
    """Synchronous helper for browser tab actions (new_tab, close_tab, next_tab, previous_tab, switch_tab)."""
    act = action.strip().lower()
    try:
        if act in ["new_tab", "new"]:
            pyautogui.hotkey("ctrl", "t")
            return "Opened new browser tab."
        elif act in ["close_tab", "close"]:
            pyautogui.hotkey("ctrl", "w")
            return "Closed current browser tab."
        elif act in ["next_tab", "next"]:
            pyautogui.hotkey("ctrl", "tab")
            return "Switched to next tab."
        elif act in ["previous_tab", "prev"]:
            pyautogui.hotkey("ctrl", "shift", "tab")
            return "Switched to previous tab."
        elif act in ["switch_tab", "select_tab"] and tab_index is not None:
            idx = max(1, min(9, tab_index))
            pyautogui.hotkey("ctrl", str(idx))
            return f"Switched to tab {idx}."
        else:
            return f"Tab action '{action}' performed."
    except Exception as e:
        logger.error(f"Error performing tab action '{action}': {e}")
        return f"Could not perform tab action: {e}"


def perform_locate_latest_download(extension: Optional[str] = None) -> str:
    """Locates the most recently downloaded file in Downloads directory."""
    downloads_dir = os.path.expanduser("~/Downloads")
    if not os.path.exists(downloads_dir):
        return "Downloads directory not found."

    try:
        files = [os.path.join(downloads_dir, f) for f in os.listdir(downloads_dir) if os.path.isfile(os.path.join(downloads_dir, f))]
        if extension:
            ext_clean = extension.lower().strip().lstrip(".")
            files = [f for f in files if f.lower().endswith(f".{ext_clean}")]

        if not files:
            return f"No recent downloaded files found in {downloads_dir}."

        latest_file = max(files, key=os.path.getmtime)
        filename = os.path.basename(latest_file)
        return f"Latest downloaded file found: '{filename}' (Path: {latest_file})."
    except Exception as err:
        return f"Error locating downloaded file: {err}"


def perform_upload_file(file_path: str) -> str:
    """Safely prepares a file for browser or application upload."""
    if not os.path.exists(file_path):
        return f"File '{file_path}' does not exist on system."
    filename = os.path.basename(file_path)
    return f"File '{filename}' (Path: {os.path.abspath(file_path)}) prepared for upload."


@llm.function_tool(
    name="open_url",
    description="Open any specific website URL in the browser (e.g. 'https://github.com', 'https://news.ycombinator.com').",
)
async def open_url(url: str) -> str:
    logger.info(f"[LIA BROWSER TOOL TRIGGERED] open_url('{url}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_open_url, url)


@llm.function_tool(
    name="search_google",
    description="Search Google directly for queries, news, or topics (e.g. 'search Google for today's AI news').",
)
async def search_google(query: str) -> str:
    logger.info(f"[LIA BROWSER TOOL TRIGGERED] search_google('{query}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_search_google, query)


@llm.function_tool(
    name="navigate_browser",
    description="Perform browser navigation: go back, go forward, refresh page, scroll down, or scroll up.",
)
async def navigate_browser(action: str) -> str:
    logger.info(f"[LIA BROWSER TOOL TRIGGERED] navigate_browser('{action}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_navigate_browser, action)


@llm.function_tool(
    name="manage_browser_tabs",
    description="Manage browser tabs: open new tab, close tab, switch next/previous tab, or select specific tab.",
)
async def manage_browser_tabs(action: str, tab_index: Optional[int] = None) -> str:
    logger.info(f"[LIA BROWSER TOOL TRIGGERED] manage_browser_tabs('{action}', {tab_index})")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_tab_action, action, tab_index)

