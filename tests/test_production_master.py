"""
Comprehensive Production Master Test Suite for LIA
Validates Health System, Process Manager, System Tray, Global Hotkey, Voice State Machine,
Tool Result Formatting, Action Verification, Security Allowlists, and Memory/Context Integration.
"""

import os
import json
import time
import pytest
import urllib.request
import asyncio
from http.client import HTTPResponse

from process_manager import get_process_manager, LIAProcessManager
from voice.state_machine import get_state_machine, VoiceStateMachine, LIAState
from hotkey import get_hotkey_manager, LIAHotkeyManager
from system_tray import create_status_icon, LIASystemTray
from tools.tool_result import create_tool_result, verify_file_created, verify_process_running
from mobile.server import run_mobile_server
from security.validation import validate_tool_call, sanitize_output, mask_secrets
from memory.manager import get_memory_manager
from brain.context import get_context_manager
from brain.orchestrator import LIAOrchestrator, IntentType


@pytest.fixture(scope="module")
def start_test_server():
    """Starts the LIA HTTP server on port 8080 for health check testing."""
    server = run_mobile_server(port=8080, daemon=True)
    time.sleep(1.5)
    yield server



def test_health_and_status_endpoints(start_test_server):
    """Test /health and /status HTTP endpoints return structured JSON status."""
    for path in ["/health", "/status"]:
        url = f"http://localhost:8080{path}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["backend"] == "online"
            assert "components" in data
            assert "livekit" in data["components"]
            assert "database" in data["components"]
            assert "device_registry" in data["components"]
            assert "voice_system" in data["components"]


def test_process_manager_lifecycle():
    """Test process manager lock handling and status checking."""
    pm = get_process_manager()
    status = pm.status()
    assert "running" in status
    assert "pid" in status

    # Test lock creation and removal cleanly
    test_pid = 999999
    pm._write_lock(test_pid)
    lock_data = pm._read_lock()
    assert lock_data.get("pid") == test_pid

    pm._clear_lock()
    assert not os.path.exists(pm.lock_file)


def test_voice_state_machine_and_watchdog():
    """Test VoiceStateMachine transitions and watchdog auto-recovery."""
    sm = VoiceStateMachine(watchdog_timeout_seconds=0.2)
    assert sm.get_state() == LIAState.IDLE

    # Register transition callback
    transitions = []
    sm.add_listener(lambda old, new: transitions.append((old, new)))

    # Perform state transition
    sm.set_state(LIAState.LISTENING)
    assert sm.get_state() == LIAState.LISTENING
    assert (LIAState.IDLE, LIAState.LISTENING) in transitions

    # Wait for watchdog auto-recovery timeout
    time.sleep(0.3)
    # Getting state triggers watchdog check
    current_state = sm.get_state()
    assert current_state == LIAState.IDLE


def test_system_tray_icon_generation():
    """Test system tray status icon generation for various states."""
    for color in ["cyan", "green", "orange", "red", "gray"]:
        icon = create_status_icon(color)
        assert icon.size == (64, 64)


def test_global_hotkey_manager_initialization():
    """Test LIAHotkeyManager instantiation and registration logic."""
    sm = get_state_machine()
    sm.set_state(LIAState.IDLE)
    
    pressed = False
    def on_press():
        nonlocal pressed
        pressed = True

    hk = LIAHotkeyManager(on_hotkey_pressed=on_press)
    # Simulate hotkey press
    hk._handle_hotkey()
    assert sm.get_state() == LIAState.LISTENING
    assert pressed is True

    # Second press interrupts / resets to IDLE
    hk._handle_hotkey()
    assert sm.get_state() == LIAState.IDLE


def test_tool_result_wrapper_and_verification():
    """Test structured tool output schema and empirical verification functions."""
    res = create_tool_result(
        tool="desktop",
        action="open_application",
        success=True,
        result="Opened Chrome",
        duration=0.15
    )
    assert res["success"] is True
    assert res["tool"] == "desktop"
    assert res["action"] == "open_application"
    assert res["duration"] == 0.15

    # Test file verification helper
    tmp_file = os.path.abspath("test_dummy_verification.txt")
    with open(tmp_file, "w") as f:
        f.write("test content")
    
    assert verify_file_created(tmp_file, max_wait_seconds=0.5) is True
    if os.path.exists(tmp_file):
        os.remove(tmp_file)

    # Test process verification helper
    assert verify_process_running(["python"], max_wait_seconds=0.5) is True


def test_security_allowlist_and_secret_masking():
    """Test security tool validation, command allowlisting, and secret masking."""
    # Test valid tool validation
    is_valid, msg, args = validate_tool_call("open_application", {"app_name": "chrome"})
    assert is_valid is True

    # Test invalid / unauthorized command
    is_valid_bad, msg_bad, args_bad = validate_tool_call("open_application", {"app_name": "rm -rf /"})
    assert is_valid_bad is False

    # Secret masking test
    masked = mask_secrets("LIVEKIT_API_SECRET=my_super_secret_key_12345")
    assert "my_super_secret_key_12345" not in masked
    assert "REDACTED" in masked


def test_memory_and_context_persistence():
    """Test long-term memory persistence and context reference resolution."""
    mem_mgr = get_memory_manager()
    res = mem_mgr.save_memory(
        key="user_voice",
        value="Warm Female Nova",
        category="preferences"
    )
    assert any(kw in res for kw in ["Remembered", "Successfully", "Saved", "updated", "memory"])

    recalled = mem_mgr.get_memory(key="user_voice")
    assert recalled is not None and recalled.get("value") == "Warm Female Nova"

    # Context engine turn & pronoun resolution check
    ctx_mgr = get_context_manager()
    ctx_mgr.add_turn("user", "search for MERN stack jobs")
    ctx_mgr.add_turn("assistant", "Found 3 MERN stack job results: 1. Lead Developer, 2. Senior React Engineer")
    
    from brain.reference_resolver import ReferenceResolver
    resolver = ReferenceResolver(ctx_mgr)
    resolved = resolver.resolve("summarize the second result")
    assert resolved.get("selected_index") == 1
