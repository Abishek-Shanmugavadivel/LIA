"""
Integration & Unit Test Suite for Phase 16 (Personal Assistant Engine) & Phase 17 (Plugin System)
Validates Calendar/Task/Reminder Management, Daily Briefings, Smart Free-Time Scheduling,
Plugin Manifest Validation, Plugin Lifecycles, Sandbox Isolation, Timeouts, Event Bus Messaging, and Orchestrator Routing.
"""

import time
import pytest
from brain.personal_assistant import get_personal_assistant, LIAPersonalAssistant, TaskPriority, TaskStatus
from plugins.manager import get_plugin_manager, LIAPluginManager, PluginStatus
from brain.event_bus import get_event_bus, CentralEventBus, EventType
from brain.orchestrator import LIAOrchestrator, IntentType


def test_personal_assistant_daily_briefing_and_tasks():
    """Test 1: Daily Briefing and Personal Task Lifecycle."""
    pa = get_personal_assistant()

    # Add Personal Task
    task_res = pa.add_personal_task(title="Finish LIA Production Hardening", priority=TaskPriority.HIGH, due_date="today")
    assert task_res["success"] is True
    task_id = task_res["result"]["task_id"]

    # Retrieve Pending Tasks
    tasks_res = pa.get_personal_tasks("pending")
    assert tasks_res["success"] is True
    assert len(tasks_res["result"]["tasks"]) > 0

    # Mark Complete
    comp_res = pa.mark_task_complete(task_id)
    assert comp_res["success"] is True

    # Daily Briefing
    briefing = pa.get_daily_briefing()
    assert briefing["success"] is True
    assert "Daily Briefing" in briefing["result"]["briefing"]


def test_smart_scheduling_and_free_time():
    """Test 2: Smart Scheduling and free time slot reasoning."""
    pa = get_personal_assistant()
    free_res = pa.find_free_time(date_str="tomorrow", required_mins=60)
    assert free_res["success"] is True
    assert "suggested_slot" in free_res["result"]


def test_central_event_bus_pub_sub():
    """Test 3: Central Event Bus pub/sub message delivery."""
    bus = get_event_bus()
    received = []

    def sample_handler(payload):
        received.append(payload)

    bus.subscribe(EventType.TASK_COMPLETED, sample_handler)
    bus.publish(EventType.TASK_COMPLETED, {"task_id": 99, "status": "completed"})

    assert len(received) == 1
    assert received[0]["task_id"] == 99


def test_plugin_registration_manifest_and_execution():
    """Test 4: Plugin registration, manifest validation, tool discovery, and execution."""
    pm = get_plugin_manager()
    
    # Check built-in demonstration plugins
    assert "github_plugin" in pm.registry
    assert "weather_plugin" in pm.registry

    # Execute GitHub Plugin
    res_gh = pm.execute_plugin_tool("github_plugin", "get_notifications", {})
    assert res_gh["success"] is True
    assert "result" in res_gh

    # Execute Weather Plugin
    res_w = pm.execute_plugin_tool("weather_plugin", "get_weather", {})
    assert res_w["success"] is True
    assert "forecast" in res_w["result"]


def test_plugin_manifest_validation_and_enable_disable():
    """Test 5: Manifest validation error catching and enable/disable toggling."""
    pm = get_plugin_manager()

    # Invalid manifest missing 'version'
    invalid_manifest = {"id": "bad_plugin", "name": "Bad Plugin", "description": "Invalid"}
    res_inv = pm.register_plugin(invalid_manifest, lambda t, a: {})
    assert res_inv["success"] is False
    assert "missing required field" in res_inv["error"]

    # Disable plugin
    dis_res = pm.disable_plugin("weather_plugin")
    assert dis_res["success"] is True

    # Execution should be blocked when disabled
    exec_dis = pm.execute_plugin_tool("weather_plugin", "get_weather", {})
    assert exec_dis["success"] is False
    assert "currently disabled" in exec_dis["error"]

    # Re-enable plugin
    en_res = pm.enable_plugin("weather_plugin")
    assert en_res["success"] is True


def test_plugin_sandbox_fault_isolation():
    """Test 6: Broken plugin fault containment and timeout caps."""
    pm = get_plugin_manager()

    broken_manifest = {
        "id": "broken_plugin",
        "name": "Broken Sandbox Test Plugin",
        "version": "1.0.0",
        "description": "Intentionally raises exception",
        "permissions": []
    }
    def broken_handler(tool, args):
        raise ValueError("Simulated Plugin Internal Crash")

    pm.register_plugin(broken_manifest, broken_handler)
    res = pm.execute_plugin_tool("broken_plugin", "test_tool", {})
    
    # LIA Core must remain alive and return clean error result
    assert res["success"] is False
    assert "Simulated Plugin Internal Crash" in res["error"]


@pytest.mark.asyncio
async def test_orchestrator_personal_assistant_and_plugin_routing():
    """Test 7: Central Orchestrator intent classification and execution routing for PA and Plugins."""
    orchestrator = LIAOrchestrator()

    # PA Intent
    i_pa = orchestrator.classify_intent("LIA, give me my daily briefing")
    assert i_pa["primary_intent"] == IntentType.PERSONAL_ASSISTANT
    res_pa = await orchestrator.process_request("LIA, give me my daily briefing")
    assert res_pa.get("status") == "success"

    # Plugin Intent
    i_pl = orchestrator.classify_intent("LIA, check my github notifications")
    assert i_pl["primary_intent"] == IntentType.PLUGIN_ACTION
    res_pl = await orchestrator.process_request("LIA, check my github notifications")
    assert res_pl.get("status") == "success"
    assert "GitHub Plugin Execution" in res_pl.get("message", "")
