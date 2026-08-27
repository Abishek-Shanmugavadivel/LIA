"""
Integration & Unit Test Suite for Phase 13 (Advanced Vision), Phase 14 (Autonomous Task Agent), and Phase 15 (Native Android Integration)
Validates Central Vision Engine, OCR Text Extraction, Visual Grounding, Visual Verification,
Autonomous Task Agent Planning, State Machine Transitions, Cancellation, Resume, and Native Android Sync Endpoints.
"""

import os
import sys
import json
import time
import pytest
import urllib.request

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.vision_engine import get_vision_engine, LIAVisionEngine
from brain.task_agent import get_task_agent, LIATaskAgent, TaskState
from brain.orchestrator import LIAOrchestrator, IntentType
from mobile.server import run_mobile_server


@pytest.fixture(scope="module")
def mobile_android_sync_server():
    """Starts LIA Mobile Backend server for testing Native Android sync endpoints."""
    server = run_mobile_server(port=8096, daemon=True)
    time.sleep(0.5)
    yield server


def test_vision_engine_detection_ocr_and_grounding():
    """Test Vision Engine UI element detection, OCR extraction, and visual grounding."""
    ve = get_vision_engine()
    elements = ve.detect_ui_elements()

    assert len(elements) > 0
    assert any(el["type"] in ["window", "button", "text_field"] for el in elements)

    # Test visual grounding
    grounded = ve.ground_visual_reference("click the login button")
    assert grounded is not None
    assert "login" in grounded.get("name", "").lower() or grounded.get("type") == "button"

    # Test visual verification
    verified = ve.verify_visual_action("Unknown / Desktop", timeout=0.5)
    assert isinstance(verified, bool)


@pytest.mark.asyncio
async def test_autonomous_task_agent_goal_planning_and_execution():
    """Test Autonomous Task Agent goal planning, execution loop, cancellation, and resume."""
    ta = get_task_agent()

    # Goal planning
    plan = ta.plan_goal("Fix my contact form bug")
    assert len(plan) >= 4
    assert ta.current_state in [TaskState.PLANNING, TaskState.IDLE]

    # Goal execution
    res = await ta.execute_goal("LIA, prepare project for deployment")
    assert res["success"] is True
    assert ta.current_state == TaskState.COMPLETED

    # Cancellation & Resume
    canc = ta.cancel_task()
    assert canc["success"] is True
    assert ta.current_state == TaskState.CANCELLED

    resm = ta.resume_task()
    assert resm["success"] is True
    assert ta.current_state == TaskState.EXECUTING


@pytest.mark.asyncio
async def test_orchestrator_vision_and_task_goal_routing():
    """Test Central Orchestrator classifies and routes vision and goal prompts."""
    orchestrator = LIAOrchestrator()

    # Vision Intent
    i_vision = orchestrator.classify_intent("LIA, look at my screen")
    assert i_vision["primary_intent"] == IntentType.VISION_ACTION
    res_v = await orchestrator.process_request("LIA, look at my screen")
    assert res_v.get("status") == "success"
    assert "Vision Engine" in res_v.get("message", "")

    # Goal Intent
    i_goal = orchestrator.classify_intent("LIA, prepare project for deployment")
    assert i_goal["primary_intent"] == IntentType.TASK_GOAL
    res_g = await orchestrator.process_request("LIA, prepare project for deployment")
    assert res_g.get("status") == "success"


def test_native_android_sync_endpoints(mobile_android_sync_server):
    """Test Native Android GET /api/android/sync and POST /api/android/telemetry HTTP endpoints."""
    # GET /api/android/sync
    sync_url = "http://localhost:8096/api/android/sync"
    req_sync = urllib.request.Request(sync_url)
    with urllib.request.urlopen(req_sync, timeout=8) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["status"] == "success"
        assert "android_sync" in data
        assert "task_state" in data["android_sync"]

    # POST /api/android/telemetry
    telem_url = "http://localhost:8096/api/android/telemetry"
    telem_payload = json.dumps({
        "device_id": "android_galaxy_s24",
        "battery": 92,
        "network": "5G",
        "status": "connected",
        "platform": "Android Native 14"
    }).encode("utf-8")
    req_telem = urllib.request.Request(telem_url, data=telem_payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req_telem, timeout=8) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["status"] == "success"
        assert data["device_id"] == "android_galaxy_s24"

    # POST /api/android/notifications
    notif_url = "http://localhost:8096/api/android/notifications"
    notif_payload = json.dumps({
        "title": "Task Completed",
        "message": "Project deployment preparation finished successfully."
    }).encode("utf-8")
    req_notif = urllib.request.Request(notif_url, data=notif_payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req_notif) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["status"] == "success"
        assert data["pushed"] is True
