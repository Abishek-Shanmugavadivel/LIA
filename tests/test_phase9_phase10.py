"""
Integration & Hardening Test Suite for Phase 9 (Master Integration) & Phase 10 (Production Hardening)
Validates Central Orchestrator Pipeline, Command Deduplication, Mobile Orchestration Endpoint,
Startup Manager Degraded Mode Fallback, Central Health Monitor, Task Lifecycle, and Clean Shutdown Handlers.
"""

import os
import json
import time
import pytest
import urllib.request

from brain.orchestrator import LIAOrchestrator, IntentType
from health import get_health_monitor, CentralHealthMonitor, HealthState
from tools.startup import initialize_lia_startup
from process_manager import get_process_manager
from voice.state_machine import get_state_machine, LIAState
from mobile.server import run_mobile_server


@pytest.fixture(scope="module")
def mobile_orchestrate_server():
    """Starts LIA Mobile Backend server for testing orchestration API endpoints."""
    server = run_mobile_server(port=8095, daemon=True)
    time.sleep(0.5)
    yield server


@pytest.mark.asyncio
async def test_central_orchestrator_pipeline_and_deduplication():
    """Test central orchestrator pipeline and command deduplication logic."""
    orchestrator = LIAOrchestrator()

    # First request
    res1 = await orchestrator.process_request("LIA, open Chrome on my laptop")
    assert res1.get("status") == "success" or res1.get("primary_intent") == IntentType.DESKTOP_ACTION

    # Immediate duplicate request should be deduplicated
    res_dup = await orchestrator.process_request("LIA, open Chrome on my laptop")
    assert res_dup.get("status") == "ignored"
    assert res_dup.get("deduplicated") is True

    # Sleep past 2s deduplication window
    time.sleep(2.1)
    res2 = await orchestrator.process_request("LIA, search for AI news")
    assert res2.get("status") != "ignored"


def test_mobile_orchestrate_http_endpoint(mobile_orchestrate_server):
    """Test POST /api/orchestrate HTTP endpoint routes commands to central orchestrator."""
    url = "http://localhost:8095/api/orchestrate"
    payload = json.dumps({"command": "LIA, what is my schedule today?"}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["status"] == "success"
        assert "result" in data


def test_startup_manager_and_degraded_mode_fallback():
    """Test initialize_lia_startup runs validation and returns status without throwing exceptions."""
    result = initialize_lia_startup()
    assert result["success"] is True
    assert result["status"] in [HealthState.HEALTHY, HealthState.DEGRADED]
    assert "health" in result


def test_central_health_monitor_breakdown():
    """Test CentralHealthMonitor returns structured status breakdown for all subsystems."""
    monitor = get_health_monitor()
    health = monitor.check_health(force_refresh=True)

    assert health["status"] in [HealthState.HEALTHY, HealthState.DEGRADED, HealthState.OFFLINE]
    assert "components" in health
    comps = health["components"]
    assert "core" in comps
    assert "ai" in comps
    assert "voice" in comps
    assert "desktop" in comps
    assert "database" in comps
    assert "network" in comps
    assert "device_registry" in comps


def test_task_lifecycle_and_state_transitions():
    """Test Task Lifecycle state machine transition sequence."""
    sm = get_state_machine()
    sm.set_state(LIAState.IDLE)
    assert sm.get_state() == LIAState.IDLE

    sm.set_state(LIAState.LISTENING)
    assert sm.get_state() == LIAState.LISTENING

    sm.set_state(LIAState.THINKING)
    assert sm.get_state() == LIAState.THINKING

    sm.set_state(LIAState.EXECUTING)
    assert sm.get_state() == LIAState.EXECUTING

    sm.set_state(LIAState.SPEAKING)
    assert sm.get_state() == LIAState.SPEAKING

    sm.set_state(LIAState.IDLE)
    assert sm.get_state() == LIAState.IDLE


def test_process_manager_shutdown_registration():
    """Test process manager shutdown signal registration."""
    pm = get_process_manager()
    pm.register_shutdown_handlers()
    status = pm.status()
    assert isinstance(status, dict)
