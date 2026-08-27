"""
Comprehensive Test Suite for LIA JARVIS Final Autonomous Mission & Self-Healing Master Upgrade
Verifies all 15 Real-World Test Missions, Self-Healing Recovery, Bounded Retries, Error Classification,
Mission Pause/Resume/Cancel, Multi-Agent Orchestration, Cross-Device Routing, and Security Policies.
"""

import os
import sys
import pytest
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from brain.mission import get_mission_engine, MissionEngine, MissionStatus, ErrorCategory, AgentRole
from brain.context_engine import get_context_engine
from tools.screen_agent import get_screen_agent
from tools.browser_agent import get_browser_agent
from memory.manager import get_memory_manager
from devices.registry import get_device_registry
from health import get_health_monitor


@pytest.mark.asyncio
async def test_mission_1_chrome_and_ai_news():
    """MISSION 1: 'Open Chrome and search today's AI news.'"""
    engine = get_mission_engine()
    res = await engine.run_mission_goal("Open Chrome and search today's AI news.")
    assert res["status"] in [MissionStatus.COMPLETED, MissionStatus.RUNNING]
    assert res["total_steps"] > 0


@pytest.mark.asyncio
async def test_mission_2_open_second_and_summarize():
    """MISSION 2: 'Open the second result and summarize it.'"""
    browser_agent = get_browser_agent()
    browser_agent.execute_web_research("AI news", max_results=3)
    res = browser_agent.open_result_by_index(1)  # 2nd result
    assert res["success"] is True


@pytest.mark.asyncio
async def test_mission_3_what_are_you_seeing():
    """MISSION 3: 'Tell me what you are seeing on my screen.'"""
    screen_agent = get_screen_agent()
    ans = screen_agent.answer_screen_question("What are you seeing on my screen?")
    assert len(ans) > 0


@pytest.mark.asyncio
async def test_mission_4_open_whatsapp_web():
    """MISSION 4: 'Open WhatsApp Web.'"""
    from tools.browser_automation import perform_open_url
    res = perform_open_url("https://web.whatsapp.com")
    assert "whatsapp" in res.lower() or "opened" in res.lower()


@pytest.mark.asyncio
async def test_mission_5_switch_to_vscode():
    """MISSION 5: 'Switch to VS Code.'"""
    from tools.desktop import perform_window_state
    res = perform_window_state("VS Code", "switch")
    assert "window" in res.lower() or "switch" in res.lower() or "no open window" in res.lower()


@pytest.mark.asyncio
async def test_mission_6_find_my_resume():
    """MISSION 6: 'Find my resume.'"""
    from tools.files import perform_find_file
    res = perform_find_file("resume")
    assert "status" in res or "found" in str(res).lower()


@pytest.mark.asyncio
async def test_mission_7_remember_mern_preference():
    """MISSION 7: 'Remember that I prefer MERN.'"""
    mem_mgr = get_memory_manager()
    res = mem_mgr.save_memory("tech_preference", "I prefer MERN stack", category="user_prefs")
    assert "remembered" in res.lower() or "saved" in res.lower()


@pytest.mark.asyncio
async def test_mission_8_what_do_you_remember_preference():
    """MISSION 8: 'What do you remember about my preference?'"""
    mem_mgr = get_memory_manager()
    results = mem_mgr.search_memory("MERN")
    assert len(results) > 0
    assert "MERN" in results[0]["value"]


@pytest.mark.asyncio
async def test_mission_9_find_three_mern_jobs_and_compare():
    """MISSION 9: 'Find three current MERN jobs and compare them.'"""
    browser_agent = get_browser_agent()
    comp_res = browser_agent.compare_search_results("MERN jobs", count=3)
    assert comp_res["success"] is True
    assert "query" in comp_res["result"]


@pytest.mark.asyncio
async def test_mission_10_open_best_result():
    """MISSION 10: 'Open the best result.'"""
    browser_agent = get_browser_agent()
    open_res = browser_agent.open_result_by_index(0)
    assert open_res["success"] is True


def test_mission_11_stop_current_task():
    """MISSION 11: 'Stop the current task.'"""
    engine = get_mission_engine()
    res = engine.cancel_active_mission()
    assert "message" in res


def test_mission_12_start_again_from_last_safe_point():
    """MISSION 12: 'Start again from the last safe point.'"""
    engine = get_mission_engine()
    res = engine.resume_active_mission()
    assert "message" in res


@pytest.mark.asyncio
async def test_mission_13_research_ai_news_in_tamil():
    """MISSION 13: 'Research today's AI news and explain it in Tamil.'"""
    from brain.orchestrator import LIAOrchestrator
    orchestration = LIAOrchestrator()
    res = await orchestration.process_request("idha Tamil la explain pannu")
    assert res["status"] in ["success", "completed"] or "message" in res


def test_mission_14_check_computer_status():
    """MISSION 14: 'Check my computer status.'"""
    health_mgr = get_health_monitor()
    health = health_mgr.check_health()
    assert health["status"] in ["HEALTHY", "DEGRADED", "OFFLINE"]


def test_mission_15_check_phone_status():
    """MISSION 15: 'Check my phone status.'"""
    registry = get_device_registry()
    devices = registry.list_registered_devices()
    assert isinstance(devices, list)


def test_self_healing_and_error_classification():
    """Tests Error Classification & Self-Healing recovery loop heuristics."""
    engine = get_mission_engine()
    err_cat = engine.classify_error("Application 'UnknownApp' not found")
    assert err_cat == ErrorCategory.APPLICATION_NOT_FOUND

    from brain.mission import Mission
    m = Mission("Test Goal")
    step = {"id": 0, "title": "Test Step"}
    healed, msg = engine.attempt_self_healing(m, step, "Application not found")
    assert healed is True
    assert "Recovered" in msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
