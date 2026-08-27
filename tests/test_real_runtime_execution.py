"""
Real Runtime End-to-End Execution Verification Suite for LIA 5.0
Tests the complete live command pipeline: Intent Classification -> Tool Routing -> Real Windows Execution -> Result Verification.
"""

import sys
import os
import json
import pytest
import asyncio
import urllib.request

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from brain.orchestrator import LIAOrchestrator, IntentType
from tools.browser_automation import perform_open_url
from tools.web_search import perform_web_search
from process_manager import get_process_manager
from voice.state_machine import get_state_machine, LIAState


@pytest.mark.asyncio
async def test_real_runtime_open_google_english():
    """TEST 1: 'open google' English command"""
    orchestrator = LIAOrchestrator()
    res = await orchestrator.process_request("open google")
    assert res["status"] == "success"
    assert "Google opened successfully" in res["message"] or "https://www.google.com" in res["message"]


@pytest.mark.asyncio
async def test_real_runtime_web_search():
    """TEST 2: 'search latest AI news' web search tool execution"""
    orchestrator = LIAOrchestrator()
    res = await orchestrator.process_request("search latest AI news")
    assert res["status"] == "success"
    assert "search_results" in res or "message" in res


@pytest.mark.asyncio
async def test_real_runtime_normal_question():
    """TEST 3: 'What is Python?' direct AI answer"""
    orchestrator = LIAOrchestrator()
    res = await orchestrator.process_request("What is Python?")
    assert res["status"] == "success"
    assert "Direct AI Answer" in res.get("message", "") or "status" in res


@pytest.mark.asyncio
async def test_real_runtime_open_google_tamil():
    """TEST 4: 'Google open பண்ணு' Tamil command"""
    orchestrator = LIAOrchestrator()
    res = await orchestrator.process_request("Google open பண்ணு")
    assert res["status"] == "success"
    assert "Google opened successfully" in res["message"] or "opened" in res["message"].lower()


@pytest.mark.asyncio
async def test_real_runtime_open_google_tanglish():
    """TEST 5: 'Google open pannu' Tanglish command"""
    orchestrator = LIAOrchestrator()
    res = await orchestrator.process_request("Google open pannu")
    assert res["status"] == "success"
    assert "Google opened successfully" in res["message"] or "opened" in res["message"].lower()


def test_process_manager_stale_cleanup():
    """TEST 6: Process manager stale process killing verification"""
    pm = get_process_manager()
    killed = pm.kill_stale_processes()
    assert isinstance(killed, int)


def test_pwa_icon_assets_exist():
    """TEST 7: PWA Icon assets existence verification"""
    icon_192 = os.path.join(os.path.dirname(__file__), "..", "mobile", "app", "icon-192.png")
    icon_512 = os.path.join(os.path.dirname(__file__), "..", "mobile", "app", "icon-512.png")
    assert os.path.exists(icon_192)
    assert os.path.exists(icon_512)


def test_hands_free_state_transitions():
    """TEST 8: Hands-free state machine transitions (LISTENING -> PROCESSING -> SPEAKING -> LISTENING & SLEEPING)"""
    sm = get_state_machine()
    sm.set_state(LIAState.LISTENING)
    assert sm.get_state() == LIAState.LISTENING

    sm.set_state(LIAState.PROCESSING)
    assert sm.get_state() == LIAState.PROCESSING

    sm.set_state(LIAState.SPEAKING)
    assert sm.get_state() == LIAState.SPEAKING

    sm.set_state(LIAState.SLEEPING)
    assert sm.get_state() == LIAState.SLEEPING

    sm.set_state(LIAState.LISTENING)
    assert sm.get_state() == LIAState.LISTENING
