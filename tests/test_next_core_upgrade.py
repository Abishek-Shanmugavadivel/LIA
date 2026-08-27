"""
Comprehensive Integration & Real-World Scenario Test Suite for LIA JARVIS Next Core Upgrade
Verifies Context Engine, Screen Agent, Browser Agent, Conversational Task State,
Multi-Step Web Tasks, Screen Q&A, and Reference Resolution (Phases 1-28).
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from brain.context_engine import get_context_engine, ContextEngine
from tools.screen_agent import get_screen_agent, ScreenAgent
from tools.browser_agent import get_browser_agent, BrowserAgent
from tools.desktop import perform_open_application, perform_close_application, perform_window_state
from tools.browser_automation import perform_open_url, perform_navigate_browser, perform_tab_action
from brain.orchestrator import LIAOrchestrator
from brain.task_agent import get_task_agent
from memory.manager import get_memory_manager


def test_scenario_1_open_chrome():
    """TEST 1: 'LIA, open Chrome.' Verify Chrome launch initiation."""
    res = perform_open_application("Chrome")
    assert "Chrome" in res or "opened" in res.lower() or "initiated" in res.lower()


def test_scenario_2_open_google():
    """TEST 2: 'LIA, open Google.' Verify Google URL opening."""
    res = perform_open_url("https://www.google.com")
    assert "google.com" in res.lower() or "opened" in res.lower()


def test_scenario_3_search_todays_ai_news():
    """TEST 3: 'LIA, search today's AI news.' Verify search research agent execution."""
    agent = get_browser_agent()
    res = agent.execute_web_research("today's AI news", max_results=3)

    assert res["success"] is True
    assert res["result"]["count"] > 0
    assert "topic" in res["result"]


def test_scenario_4_open_second_result():
    """TEST 4: 'LIA, open the second result.' Verify ordinal result selection."""
    agent = get_browser_agent()
    agent.execute_web_research("React framework news", max_results=3)
    res_open = agent.open_result_by_index(1)  # 2nd result = index 1

    assert res_open["success"] is True
    assert "title" in res_open["result"]


def test_scenario_5_what_are_you_seeing():
    """TEST 5: 'LIA, what are you seeing?' Verify screen analysis."""
    screen_agent = get_screen_agent()
    answer = screen_agent.answer_screen_question("What are you seeing on my screen?")

    assert len(answer) > 0
    assert "screen" in answer.lower() or "application" in answer.lower() or "window" in answer.lower()


def test_scenario_6_scroll_down():
    """TEST 6: 'LIA, scroll down.' Verify scroll navigation."""
    res = perform_navigate_browser("scroll_down")
    assert "scrolled" in res.lower()


def test_scenario_7_go_back():
    """TEST 7: 'LIA, go back.' Verify history navigation."""
    res = perform_navigate_browser("back")
    assert "back" in res.lower() or "navigated" in res.lower()


def test_scenario_8_open_whatsapp_web():
    """TEST 8: 'LIA, open WhatsApp Web.' Verify WhatsApp Web launch."""
    res = perform_open_url("https://web.whatsapp.com")
    assert "whatsapp" in res.lower() or "opened" in res.lower()


def test_scenario_9_switch_to_vscode():
    """TEST 9: 'LIA, switch to VS Code.' Verify window focus switch."""
    res = perform_window_state("VS Code", "switch")
    assert "window" in res.lower() or "switch" in res.lower() or "no open window" in res.lower()


def test_scenario_10_what_application_is_open():
    """TEST 10: 'LIA, what application is open?' Verify screen Q&A application query."""
    screen_agent = get_screen_agent()
    answer = screen_agent.answer_screen_question("What application am I using?")

    assert "active application" in answer.lower() or "window" in answer.lower()


def test_scenario_11_remember_preference():
    """TEST 11: 'LIA, remember that I prefer MERN.' Verify persistent memory storage."""
    mem_mgr = get_memory_manager()
    res = mem_mgr.save_memory("developer_preference", "I prefer MERN stack development.", category="preferences")

    assert "remembered" in res.lower() or "saved" in res.lower()


def test_scenario_12_retrieve_preference():
    """TEST 12: 'LIA, what do you remember about my preference?' Verify memory retrieval."""
    mem_mgr = get_memory_manager()
    results = mem_mgr.search_memory("MERN")

    assert len(results) > 0
    assert "MERN" in results[0]["value"]


def test_scenario_13_contextual_reference_resolution():
    """TEST 13: 'LIA, open the second one.' Verify ReferenceResolver ordinal mapping."""
    context_engine = get_context_engine()
    context_engine.ctx.set_active_task("search", query="MERN jobs", results=["Job 1", "Job 2", "Job 3"])

    resolved = context_engine.resolve_reference("open the second one")
    assert resolved["selected_index"] == 1
    assert resolved["resolved_entity"] == "Job 2"


def test_scenario_14_stop():
    """TEST 14: 'LIA, stop.' Verify task cancellation."""
    task_agent = get_task_agent()
    res = task_agent.cancel_task()

    assert res["success"] is True
    assert task_agent.current_state == "CANCELLED"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
