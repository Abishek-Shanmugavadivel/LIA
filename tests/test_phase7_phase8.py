"""
Comprehensive Test Suite for Phase 7 (Mobile Integration) & Phase 8 (Final Unified System)
Validates Security Engine, Device Registry, Mobile Token Backend, Mobile Tools, Central Orchestrator,
Wake Word System, and Unified Multilingual Memory.
"""

import os
import json
import pytest
import time
from urllib.request import urlopen, Request

from security.permissions import check_permission, PermissionLevel, HIGH_RISK_COMMANDS
from security.validation import validate_tool_call, mask_secrets, sanitize_output
from devices.registry import DeviceRegistry, get_device_registry
from devices.desktop import DesktopDevice
from devices.mobile import MobileDevice
from mobile.server import generate_mobile_token, run_mobile_server
from tools.mobile import get_mobile_status, send_mobile_notification, get_device_list, route_device_command
from brain.orchestrator import LIAOrchestrator, IntentType
from voice.wakeword import WakeWordDetector, ConversationMode
from tools.memory_tools import remember_information, recall_memory, list_all_memories, forget_memory


def test_security_engine():
    """Test permission checks, parameter validation, secret masking, and high-risk command blocking."""
    # 1. Safe tool check
    perm, reason = check_permission("open_application", {"app_name": "chrome"})
    assert perm == PermissionLevel.SAFE

    # 2. High-risk command check
    perm_risk, _ = check_permission("format_disk", {})
    assert perm_risk == PermissionLevel.HIGH_RISK

    # 3. Malicious pattern / credential store check
    perm_bad, _ = check_permission("remember_information", {"category": "secrets", "content": "my_api_key = 12345"})
    assert perm_bad == PermissionLevel.BLOCKED

    # 4. Secret redaction test
    text = "LIVEKIT_API_SECRET=my_super_secret_12345678 and key GOOGLE_API_KEY=AIzaSy123456789012345678901234567890123"
    masked = mask_secrets(text)
    assert "my_super_secret" not in masked
    assert "[REDACTED" in masked


def test_device_registry():
    """Test device registration, state tracking, and target normalization."""
    registry = get_device_registry()
    
    # Register desktop
    desktop = registry.register_device(
        device_id="desktop_test_01",
        name="Test Workstation",
        device_type="desktop",
        platform="Windows",
        battery=100
    )
    assert desktop["id"] == "desktop_test_01"
    assert desktop["status"] == "connected"

    # Register mobile
    mobile = registry.register_device(
        device_id="mobile_test_01",
        name="Test Phone",
        device_type="mobile",
        platform="Android",
        battery=88,
        network="Wi-Fi"
    )
    assert mobile["battery"] == 88

    # Target normalization
    assert registry.normalize_device_target("my laptop") == "desktop"
    assert registry.normalize_device_target("my computer") == "desktop"
    assert registry.normalize_device_target("my phone") == "mobile"
    assert registry.normalize_device_target("android phone") == "mobile"


def test_mobile_token_generation():
    """Test secure token generation without exposing API secrets."""
    os.environ["LIVEKIT_API_KEY"] = "test_api_key_123"
    os.environ["LIVEKIT_API_SECRET"] = "test_api_secret_1234567890123456"

    token = generate_mobile_token(identity="mobile_unit_test", room_name="test_room")
    assert isinstance(token, str)
    assert len(token) > 50
    assert "test_api_secret" not in token  # Secret is signed into JWT, not exposed as plaintext


def test_mobile_http_server():
    """Test running mobile HTTP token & telemetry server endpoints."""
    os.environ["LIVEKIT_API_KEY"] = "test_api_key_123"
    os.environ["LIVEKIT_API_SECRET"] = "test_api_secret_1234567890123456"

    server = run_mobile_server(port=8089, daemon=True)
    time.sleep(0.3)

    try:
        # GET token endpoint
        req = Request("http://localhost:8089/api/mobile/token")
        with urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "success"
            assert "token" in data

        # POST telemetry status endpoint
        post_data = json.dumps({
            "device_id": "mobile_http_test",
            "battery": 92,
            "network": "5G",
            "platform": "iOS",
            "name": "User's iPhone"
        }).encode("utf-8")
        req_post = Request("http://localhost:8089/api/mobile/status", data=post_data, headers={"Content-Type": "application/json"})
        with urlopen(req_post) as resp_post:
            data_post = json.loads(resp_post.read().decode("utf-8"))
            assert data_post["status"] == "success"

    finally:
        try:
            server.server_close()
        except Exception:
            pass



@pytest.mark.asyncio
async def test_mobile_tools():
    """Test LLM tools for mobile status, notifications, and device listing."""
    # 1. Mobile status
    status = await get_mobile_status()
    assert status["status"] == "success"
    assert "battery_percentage" in status

    # 2. Send notification
    notif = await send_mobile_notification("Test Alert", "LIA Mobile Integration Works!")
    assert notif["status"] == "success"
    assert notif["notification"]["title"] == "Test Alert"

    # 3. Device list
    dev_list = await get_device_list()
    assert dev_list["status"] == "success"
    assert dev_list["device_count"] >= 1

    # 4. Route command
    route_res = await route_device_command("laptop", "open Chrome")
    assert route_res["status"] == "success"
    assert route_res["target_category"] == "desktop"


@pytest.mark.asyncio
async def test_central_orchestrator():
    """Test intent classification, multi-step parsing, and security validation routing."""
    orchestrator = LIAOrchestrator()

    # Intent classification
    c1 = orchestrator.classify_intent("What is React?")
    assert c1["primary_intent"] == IntentType.AI_ANSWER

    c2 = orchestrator.classify_intent("LIA, search for the latest MERN jobs")
    assert c2["primary_intent"] == IntentType.WEB_SEARCH

    c3 = orchestrator.classify_intent("LIA, open Chrome on my laptop")
    assert c3["primary_intent"] == IntentType.DESKTOP_ACTION
    assert c3["target_device"] == "desktop"

    c4 = orchestrator.classify_intent("LIA, what's my phone battery?")
    assert c4["primary_intent"] == IntentType.MOBILE_ACTION

    c5 = orchestrator.classify_intent("LIA, is my laptop connected?")
    assert c5["primary_intent"] == IntentType.DEVICE_QUERY

    # Multi-step parsing
    steps = orchestrator.parse_multistep_task("open Chrome on my laptop and search for MERN jobs and tell me the results")
    assert len(steps) >= 2

    # Single-step process execution
    res = await orchestrator.process_request("LIA, what's my phone battery?")
    assert res["status"] == "success"


def test_wake_word_system():
    """Test wake word keyword detection, conversation modes, and interruption handling."""
    detector = WakeWordDetector(mode=ConversationMode.WAKE_WORD)

    # 1. No wake word
    d1 = detector.process_transcript("What is the weather today?")
    assert d1["activated"] == False

    # 2. Wake word trigger
    d2 = detector.process_transcript("Hey LIA, open Chrome")
    assert d2["activated"] == True
    assert "open chrome" in d2["cleaned_prompt"].lower()

    # 3. Interruption word
    d3 = detector.process_transcript("Okay stop")
    assert d3["is_interruption"] == True


@pytest.mark.asyncio
async def test_unified_multilingual_memory():
    """Test unified memory persistence across English, Tamil, and Tanglish."""
    # 1. Store English memory
    mem_en = await remember_information(key="preferred_browser", value="Chrome is my preferred browser.", category="preference")
    assert "remembered" in str(mem_en).lower() or "saved" in str(mem_en).lower()

    # 2. Store Tamil / Tanglish memory
    mem_ta = await remember_information(key="developer_profile", value="LIA, naan MERN stack developer dahn.", category="profile")
    assert "remembered" in str(mem_ta).lower() or "saved" in str(mem_ta).lower()

    # 3. Recall memory
    recalled = await recall_memory("preferred browser")
    assert "chrome" in str(recalled).lower() or "preferred" in str(recalled).lower()

    # 4. Clean up test memories
    await forget_memory("preferred_browser")
    await forget_memory("developer_profile")
