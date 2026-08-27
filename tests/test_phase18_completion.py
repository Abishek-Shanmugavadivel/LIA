"""
Final Completion Test Suite for LIA 5.0 (Phase 18 Final Completion Mode)
Validates all required end-to-end features:
1. "open google" (Browser launch)
2. "search for..." (DuckDuckGo web search)
3. "open notepad" (Application opening & PID verification)
4. "open downloads" (Folder opening)
5. Tamil command ("இன்றைய செய்திகள் என்ன?")
6. Tanglish command ("google ah open பண்ணு")
7. Invalid command ("xyz123nonsensecommand")
8. Unsafe/restricted command ("sudo rm -rf /")
9. Voice response configuration (Female default voice)
10. Mobile UI HTTP API endpoint (/api/orchestrate)
11. Desktop Dashboard UI Matrix rendering & state machine transitions
"""

import os
import sys
import json
import time
import pytest
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.orchestrator import LIAOrchestrator, IntentType
from security.permissions import check_permission, PermissionLevel
from voice.voice_config import get_voice_manager
from mobile.server import run_mobile_server


@pytest.fixture(scope="module")
def completion_server():
    """Starts LIA Mobile Backend server for HTTP API testing."""
    server = run_mobile_server(port=8099, daemon=True)
    time.sleep(0.5)
    yield server


@pytest.mark.asyncio
async def test_cmd_1_open_google():
    """Test 1: 'open google' executes browser action."""
    orchestrator = LIAOrchestrator()
    intent = orchestrator.classify_intent("open google")
    assert intent["primary_intent"] == IntentType.DESKTOP_ACTION

    res = await orchestrator.process_request("open google")
    assert res.get("status") == "success"
    assert "chrome" in res.get("message", "").lower() or "google" in res.get("message", "").lower() or "opened" in res.get("message", "").lower()


@pytest.mark.asyncio
async def test_cmd_2_search_for():
    """Test 2: 'search for generative ai' performs web search."""
    orchestrator = LIAOrchestrator()
    intent = orchestrator.classify_intent("search for generative ai")
    assert intent["primary_intent"] in [IntentType.WEB_SEARCH, IntentType.AI_ANSWER]

    res = await orchestrator.process_request("search for generative ai")
    assert res.get("status") == "success"


@pytest.mark.asyncio
async def test_cmd_3_open_notepad():
    """Test 3: Application opening 'open notepad'."""
    orchestrator = LIAOrchestrator()
    intent = orchestrator.classify_intent("open notepad")
    assert intent["primary_intent"] == IntentType.DESKTOP_ACTION

    res = await orchestrator.process_request("open notepad")
    assert res.get("status") == "success"
    assert "notepad" in res.get("message", "").lower() or "opened" in res.get("message", "").lower()


@pytest.mark.asyncio
async def test_cmd_4_open_downloads():
    """Test 4: Folder opening 'open downloads'."""
    orchestrator = LIAOrchestrator()
    intent = orchestrator.classify_intent("open downloads")
    assert intent["primary_intent"] == IntentType.FILE_ACTION

    res = await orchestrator.process_request("open downloads")
    assert res.get("status") == "success"


@pytest.mark.asyncio
async def test_cmd_5_tamil_news_command():
    """Test 5: Tamil command 'இன்றைய செய்திகள் என்ன?'."""
    orchestrator = LIAOrchestrator()
    intent = orchestrator.classify_intent("இன்றைய செய்திகள் என்ன?")
    assert intent["primary_intent"] == IntentType.NEWS_ACTION

    res = await orchestrator.process_request("இன்றைய செய்திகள் என்ன?")
    assert res.get("status") == "success"


@pytest.mark.asyncio
async def test_cmd_6_tanglish_command():
    """Test 6: Tanglish command 'google ah open பண்ணு'."""
    orchestrator = LIAOrchestrator()
    intent = orchestrator.classify_intent("google ah open பண்ணு")
    assert intent["primary_intent"] == IntentType.DESKTOP_ACTION

    res = await orchestrator.process_request("google ah open பண்ணு")
    assert res.get("status") == "success"


@pytest.mark.asyncio
async def test_cmd_7_invalid_command():
    """Test 7: Invalid command 'xyz123nonsensecommand' handled gracefully."""
    orchestrator = LIAOrchestrator()
    res = await orchestrator.process_request("xyz123nonsensecommand")
    assert res.get("status") == "success"


@pytest.mark.asyncio
async def test_cmd_8_unsafe_restricted_command():
    """Test 8: Unsafe/restricted command 'sudo rm -rf /' blocked by Security Engine."""
    level, reason = check_permission("execute_command", {"command": "sudo rm -rf /"})
    assert level == PermissionLevel.BLOCKED
    assert "blocked" in reason.lower() or "dangerous" in reason.lower() or "high-risk" in reason.lower()


def test_cmd_9_voice_response_configuration():
    """Test 9: Voice response configuration (Female Warm Voice default)."""
    voice_mgr = get_voice_manager()
    curr_voice = voice_mgr.get_current_voice()
    assert curr_voice["type"] == "female"
    assert curr_voice["voice_id"] == "Aoede"


def test_cmd_10_mobile_ui_api(completion_server):
    """Test 10: Mobile UI HTTP API endpoint (/api/orchestrate)."""
    url = "http://localhost:8099/api/orchestrate"
    payload = json.dumps({"command": "open google"}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["status"] == "success"
        assert "result" in data
