"""
Comprehensive Integration Test Suite for LIA JARVIS Computer Control Master
Verifies Application Discovery, Browser Controls, Window Management, Screen Vision,
Privacy Mode, Emergency Stop, and Multilingual Tamil/Tanglish Intent Routing.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.app_discovery import get_app_discovery_manager, ApplicationDiscoveryManager
from tools.desktop import perform_open_application, perform_close_application, perform_window_state
from tools.browser_automation import perform_open_url, perform_navigate_browser, perform_tab_action, perform_locate_latest_download, perform_upload_file
from tools.vision_engine import LIAVisionEngine
from brain.context import get_context_manager
from brain.task_agent import get_task_agent
from brain.orchestrator import LIAOrchestrator, IntentType


def test_application_discovery_manager():
    """Verifies safe dynamic Windows application discovery and safety checks."""
    app_discovery = get_app_discovery_manager()
    apps = app_discovery.discover_installed_applications(force_refresh=True)

    assert isinstance(apps, dict)
    assert len(apps) > 0
    assert "chrome" in apps or "notepad" in apps or "calculator" in apps

    # Test safety validation
    assert app_discovery.is_safe_launch_target("calc.exe") is True
    assert app_discovery.is_safe_launch_target("notepad.exe") is True
    assert app_discovery.is_safe_launch_target("rm -rf /") is False
    assert app_discovery.is_safe_launch_target("cmd.exe & format c:") is False

    # Test application search
    notepad_entry = app_discovery.find_application("notepad")
    assert notepad_entry is not None
    assert "notepad" in notepad_entry["application_name"]


def test_voice_app_and_window_control():
    """Verifies perform_open_application, perform_close_application, and window management."""
    # Test open application
    res_open = perform_open_application("calculator")
    assert "Calculator" in res_open or "opened" in res_open.lower() or "initiated" in res_open.lower()

    # Test window management
    res_win = perform_window_state("Calculator", "minimize")
    assert "Minimized" in res_win or "No open window" in res_win

    # Test close application
    res_close = perform_close_application("calculator")
    assert "closed" in res_close.lower() or "not currently running" in res_close.lower()


def test_browser_tab_and_download_controls():
    """Verifies tab action, download locator, and upload helper functions."""
    res_tab_new = perform_tab_action("new_tab")
    assert "Opened new browser tab" in res_tab_new

    res_tab_close = perform_tab_action("close_tab")
    assert "Closed current browser tab" in res_tab_close

    res_tab_switch = perform_tab_action("switch_tab", tab_index=2)
    assert "Switched to tab 2" in res_tab_switch

    res_download = perform_locate_latest_download()
    assert "download" in res_download.lower()

    # Test upload helper with temp file
    temp_file = os.path.abspath("temp_test_upload.txt")
    with open(temp_file, "w") as f:
        f.write("test content")
    try:
        res_upload = perform_upload_file(temp_file)
        assert "prepared for upload" in res_upload.lower()
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


def test_privacy_mode_and_vision_blocking():
    """Verifies Privacy Mode toggle and screen analysis blocking."""
    ctx = get_context_manager()
    vision = LIAVisionEngine()

    # Privacy Mode OFF
    ctx.privacy_mode = False
    ocr_off = vision.extract_ocr_text("dummy_path.png")
    assert "[PRIVACY MODE ACTIVE" not in ocr_off

    # Privacy Mode ON
    ctx.privacy_mode = True
    ocr_on = vision.extract_ocr_text("dummy_path.png")
    assert "[PRIVACY MODE ACTIVE" in ocr_on

    elements = vision.detect_ui_elements("dummy_path.png")
    assert elements[0]["type"] == "privacy_notice"

    # Reset Privacy Mode
    ctx.privacy_mode = False


def test_emergency_stop():
    """Verifies Emergency Stop task cancellation."""
    task_agent = get_task_agent()
    res_cancel = task_agent.cancel_task()

    assert res_cancel["success"] is True
    assert task_agent.is_cancelled is True
    assert task_agent.current_state == "CANCELLED"


def test_multilingual_tamil_tanglish_orchestration():
    """Verifies Tamil and Tanglish computer control intent classification."""
    orchestrator = LIAOrchestrator()

    # Tamil / Tanglish Vision Command
    intent1 = orchestrator.classify_intent("LIA screen la enna irukku?")
    assert intent1["primary_intent"] == IntentType.VISION_ACTION

    # Tamil / Tanglish Explain Error Command
    intent2 = orchestrator.classify_intent("LIA idha explain pannu")
    assert intent2["primary_intent"] == IntentType.VISION_ACTION

    # Emergency Stop Command
    intent3 = orchestrator.classify_intent("STOP LIA")
    assert intent3["primary_intent"] == IntentType.TASK_GOAL
    assert intent3.get("action") == "emergency_stop"

    # Privacy Mode Command
    intent4 = orchestrator.classify_intent("LIA privacy mode on")
    assert intent4["primary_intent"] == IntentType.MODE_ACTION
    assert intent4.get("action") == "privacy_mode"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
