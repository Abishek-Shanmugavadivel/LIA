"""
Comprehensive Unit Tests for LIA Tools and Conversation Manager (Phase 2, 3 & 4)
"""

import os
import sys
import asyncio
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.system import perform_get_system_info, get_system_information
from tools.browser import perform_open_website, open_website
from tools.desktop import (
    perform_open_application,
    perform_close_application,
    perform_open_folder,
    open_application,
    close_application,
    open_folder,
)
from tools.web_search import perform_web_search, web_search
from brain.conversation import ConversationManager


# ----------------------------------------------------
# System Tool Tests
# ----------------------------------------------------
def test_system_info_metrics():
    # Test CPU metric
    cpu_res = perform_get_system_info("cpu")
    assert "CPU Usage" in cpu_res

    # Test RAM metric
    ram_res = perform_get_system_info("ram")
    assert "RAM Memory" in ram_res

    # Test Disk metric
    disk_res = perform_get_system_info("disk")
    assert "Disk Storage" in disk_res

    # Test OS metric
    os_res = perform_get_system_info("os")
    assert "Operating System" in os_res

    # Test Battery metric
    battery_res = perform_get_system_info("battery")
    assert "Battery Status" in battery_res

    # Test All metrics combined
    all_res = perform_get_system_info("all")
    assert "Operating System" in all_res
    assert "CPU Usage" in all_res
    assert "RAM Memory" in all_res


@pytest.mark.asyncio
async def test_async_get_system_information():
    res = await get_system_information("cpu")
    assert "CPU Usage" in res


# ----------------------------------------------------
# Browser Tool Tests
# ----------------------------------------------------
def test_open_website_shortcuts():
    # Empty query check
    empty_res = perform_open_website("")
    assert "empty" in empty_res.lower()

    # YouTube shortcut logic check
    yt_res = perform_open_website("youtube")
    assert "youtube.com" in yt_res.lower() or "opened" in yt_res.lower()

    # Direct URL logic check
    direct_res = perform_open_website("example.com")
    assert "example.com" in direct_res.lower()


@pytest.mark.asyncio
async def test_async_open_website():
    res = await open_website("github")
    assert "github.com" in res.lower() or "opened" in res.lower()


# ----------------------------------------------------
# Desktop Tool Tests
# ----------------------------------------------------
def test_desktop_control_disallowed():
    # Disallowed app launch attempt
    bad_app = perform_open_application("malicious_app_123")
    assert "controlled application registry" in bad_app.lower() or "not in the allowed" in bad_app.lower()

    # Disallowed app close attempt
    bad_close = perform_close_application("unknown_daemon_xyz")
    assert "not permitted" in bad_close.lower() or "not supported" in bad_close.lower()

    # Disallowed folder attempt
    bad_folder = perform_open_folder("c:\\windows\\system32\\secret")
    assert "not in the safe folder allowlist" in bad_folder.lower()


def test_desktop_control_allowed_checks():
    # Safe folder test (Downloads)
    downloads_res = perform_open_folder("downloads")
    assert "downloads" in downloads_res.lower() or "opened" in downloads_res.lower()

    # Notepad close test (when not running)
    notepad_close = perform_close_application("notepad")
    assert "notepad" in notepad_close.lower()


@pytest.mark.asyncio
async def test_async_desktop_tools():
    res_app = await open_application("calc")
    assert "calc" in res_app.lower() or "opened" in res_app.lower()

    res_folder = await open_folder("desktop")
    assert "desktop" in res_folder.lower() or "opened" in res_folder.lower()


# ----------------------------------------------------
# Conversation Manager Tests
# ----------------------------------------------------
def test_conversation_manager():
    mgr = ConversationManager(max_history_turns=2)
    assert mgr.turn_count == 0

    mgr.add_user_message("Hello LIA")
    mgr.add_assistant_message("Hello! How can I help you today?")
    assert mgr.turn_count == 2

    history = mgr.get_history()
    assert len(history) == 2
    assert history[0]["content"] == "Hello LIA"

    # Test prompt formatting
    formatted = mgr.format_prompt_with_history("System Instruction")
    assert "CONVERSATION HISTORY:" in formatted
    assert "Hello LIA" in formatted

    # Test truncation when exceeding max_history_turns (2 turns = 4 messages)
    mgr.add_user_message("What is Python?")
    mgr.add_assistant_message("Python is a high-level programming language.")
    mgr.add_user_message("Explain decorators.")
    mgr.add_assistant_message("Decorators wrap functions to extend behavior.")

    assert mgr.turn_count == 4  # Truncated to max 4 messages (2 turns)

    # Test clear
    mgr.clear()
    assert mgr.turn_count == 0


if __name__ == "__main__":
    print("Running synchronous tests...")
    test_system_info_metrics()
    print("System info tests passed!")
    test_open_website_shortcuts()
    print("Browser website tests passed!")
    test_desktop_control_disallowed()
    test_desktop_control_allowed_checks()
    print("Desktop control tests passed!")
    test_conversation_manager()
    print("Conversation manager tests passed!")

    print("Running async tests...")
    asyncio.run(test_async_get_system_information())
    asyncio.run(test_async_open_website())
    asyncio.run(test_async_desktop_tools())
    print("Async tool tests passed!")

    print("\nALL LIA TOOL & CONVERSATION TESTS PASSED SUCCESSFULLY!")
