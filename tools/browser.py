"""
Browser Control Tools for LIA (Phase 4)
Handles opening popular websites or user-specified URLs in the system's default web browser.
"""

import logging
import asyncio
import webbrowser
from typing import Dict
from urllib.parse import urlparse
from livekit.agents import llm

logger = logging.getLogger("lia-tools-browser")

# Predefined website shortcuts
WEBSITE_SHORTCUTS: Dict[str, str] = {
    "youtube": "https://www.youtube.com",
    "github": "https://github.com",
    "linkedin": "https://www.linkedin.com",
    "gmail": "https://mail.google.com",
    "google": "https://www.google.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "reddit": "https://www.reddit.com",
    "stackoverflow": "https://stackoverflow.com",
    "chatgpt": "https://chatgpt.com",
}


def perform_open_website(url_or_name: str) -> str:
    """Synchronous helper to open a website in the default browser."""
    cleaned = url_or_name.strip().lower()
    if not cleaned:
        return "Website or URL was empty."

    # Check shortcut dictionary using exact name or word matching
    target_url = None
    cleaned_words = cleaned.split()
    for shortcut, link in WEBSITE_SHORTCUTS.items():
        if cleaned == shortcut or shortcut in cleaned_words:
            target_url = link
            break

    # If not in shortcuts, treat as a direct URL
    if not target_url:
        if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
            target_url = f"https://{cleaned}"
        else:
            target_url = cleaned

    logger.info(f"Opening website: '{target_url}' requested by user ('{url_or_name}')")

    try:
        webbrowser.open(target_url)
        return f"Opened {target_url} in your default browser."
    except Exception as e:
        logger.error(f"Error opening browser for '{target_url}': {e}")
        return f"Could not open website '{url_or_name}': {str(e)}"


@llm.function_tool(
    name="open_website",
    description="Open a website in the default web browser (e.g. YouTube, GitHub, LinkedIn, Gmail, Google, or any web URL).",
)
async def open_website(url: str) -> str:
    """LiveKit tool wrapper for opening websites."""
    logger.info(f"[LIA BROWSER TOOL TRIGGERED] open_website('{url}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_open_website, url)
