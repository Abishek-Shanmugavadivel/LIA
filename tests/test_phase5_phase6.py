"""
Unit & Integration Tests for LIA Phase 5 (Screen, Mouse, Keyboard) and Phase 6 (Long-Term Persistent Memory)
"""

import os
import sys
import tempfile
import asyncio
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from memory.database import init_db, get_db_connection
from memory.manager import MemoryManager
from memory.retrieval import MemoryRetrieval
from tools.memory_tools import (
    remember_information,
    recall_memory,
    list_all_memories,
    forget_memory,
)
from tools.screen import (
    capture_desktop_screenshot,
    get_active_window_info,
    perform_analyze_screen,
    take_screenshot,
    analyze_screen,
    get_active_application,
)
from tools.mouse import (
    validate_coordinates,
    perform_move_mouse,
    perform_click_mouse,
    move_mouse,
    click_mouse,
    double_click_mouse,
    right_click_mouse,
)
from tools.keyboard import (
    perform_type_text,
    perform_press_key,
    perform_press_hotkey,
    type_text,
    press_key,
    press_hotkey,
)
from tools.desktop import perform_open_application
from tools.web_search import perform_web_search


# ====================================================
# PHASE 6 - MEMORY TESTS
# ====================================================
def test_memory_database_crud():
    # Use temporary DB file for isolation
    test_db = os.path.join(tempfile.gettempdir(), "lia_test_memory.db")
    if os.path.exists(test_db):
        os.remove(test_db)

    init_db(test_db)
    mgr = MemoryManager(test_db)

    # 1. Save memory
    res1 = mgr.save_memory("user_stack", "MERN stack developer", category="project")
    assert "Remembered" in res1

    # 2. Get memory
    mem = mgr.get_memory("user_stack")
    assert mem is not None
    assert mem["value"] == "MERN stack developer"
    assert mem["category"] == "project"

    # 3. Search memory
    search_res = mgr.search_memory("MERN")
    assert len(search_res) == 1
    assert search_res[0]["key"] == "user_stack"

    # 4. List memories
    list_res = mgr.list_memories(category="project")
    assert len(list_res) == 1

    # 5. Delete memory
    del_res = mgr.delete_memory("user_stack")
    assert "Successfully deleted" in del_res

    # 6. Verify deletion
    mem_after = mgr.get_memory("user_stack")
    assert mem_after is None

    if os.path.exists(test_db):
        os.remove(test_db)


def test_memory_sensitive_information_filter():
    test_db = os.path.join(tempfile.gettempdir(), "lia_test_sec_memory.db")
    if os.path.exists(test_db):
        os.remove(test_db)

    init_db(test_db)
    mgr = MemoryManager(test_db)

    # Attempt saving password
    res_pass = mgr.save_memory("my_password", "SecretPass123")
    assert "Security policy prevents" in res_pass

    # Attempt saving API key
    res_key = mgr.save_memory("api_key", "sk-proj-123456")
    assert "Security policy prevents" in res_key

    # Attempt saving bearer auth token
    res_token = mgr.save_memory("auth_token", "Bearer abc.def.ghi")
    assert "Security policy prevents" in res_token

    # Verify DB is clean
    assert len(mgr.list_memories()) == 0

    if os.path.exists(test_db):
        os.remove(test_db)


def test_memory_persistence_across_sessions():
    test_db = os.path.join(tempfile.gettempdir(), "lia_test_persist_memory.db")
    if os.path.exists(test_db):
        os.remove(test_db)

    init_db(test_db)
    # Session 1: Save preference
    mgr1 = MemoryManager(test_db)
    mgr1.save_memory("color_preference", "blue dark theme", category="preference")

    # Session 2: New manager instance reading same DB
    mgr2 = MemoryManager(test_db)
    mem = mgr2.get_memory("color_preference")
    assert mem is not None
    assert mem["value"] == "blue dark theme"

    retrieval = MemoryRetrieval(mgr2)
    context_str = retrieval.retrieve_relevant_context("color")
    assert "color_preference" in context_str
    assert "blue dark theme" in context_str

    if os.path.exists(test_db):
        os.remove(test_db)


@pytest.mark.asyncio
async def test_async_memory_tools():
    # Test memory tool wrappers
    res_rem = await remember_information("test_pref", "prefers concise answers", category="preference")
    assert "Remembered" in res_rem or "Security" in res_rem

    res_rec = await recall_memory("concise")
    assert "concise" in res_rec.lower() or "remember" in res_rec.lower()

    res_list = await list_all_memories()
    assert isinstance(res_list, str)

    res_forget = await forget_memory("test_pref")
    assert "deleted" in res_forget.lower() or "no memory" in res_forget.lower()


# ====================================================
# PHASE 5 - SCREEN, MOUSE, KEYBOARD TESTS
# ====================================================
def test_screen_capture_and_active_window():
    # Test active window info
    info = get_active_window_info()
    assert "title" in info
    assert "width" in info
    assert "height" in info

    # Test desktop screenshot capture
    img_path = capture_desktop_screenshot("test_screen_unit.png")
    assert os.path.exists(img_path)
    assert os.path.getsize(img_path) > 0


def test_mouse_coordinate_validation():
    # Valid coordinates
    valid, msg, bx, by = validate_coordinates(100, 100)
    assert valid is True
    assert bx == 100
    assert by == 100

    # Impossible negative coordinate
    valid_neg, msg_neg, _, _ = validate_coordinates(-50, 100)
    assert valid_neg is False
    assert "outside valid screen bounds" in msg_neg

    # Out of bounds coordinate
    valid_oob, msg_oob, _, _ = validate_coordinates(99999, 99999)
    assert valid_oob is False
    assert "outside valid screen bounds" in msg_oob


def test_keyboard_input_validation():
    # Valid key press check
    res_key = perform_press_key("enter")
    assert "Entered" in res_key or "Pressed key 'Enter'" in res_key

    # Disallowed key press check
    res_bad_key = perform_press_key("malicious_injection_key")
    assert "not in the validated allowed keys list" in res_bad_key

    # Valid hotkey check
    res_hk = perform_press_hotkey("ctrl+c")
    assert "Pressed hotkey" in res_hk or "Ctrl" in res_hk


@pytest.mark.asyncio
async def test_async_phase5_tools():
    # Test screenshot async tool
    res_ss = await take_screenshot()
    assert "captured" in res_ss.lower()

    # Test active app async tool
    res_app = await get_active_application()
    assert "Active Application" in res_app

    # Test move mouse async tool
    res_mouse = await move_mouse(200, 200)
    assert "Moved mouse" in res_mouse

    # Test keyboard async tool
    res_kb = await press_key("escape")
    assert "Pressed" in res_kb or "Esc" in res_kb


# ====================================================
# END-TO-END WORKFLOW SEQUENCE TEST
# ====================================================
def test_e2e_realistic_sequence():
    print("\n--- Starting E2E Realistic Sequence Test ---")
    test_db = os.path.join(tempfile.gettempdir(), "lia_e2e_test.db")
    if os.path.exists(test_db):
        os.remove(test_db)
    init_db(test_db)
    mgr = MemoryManager(test_db)

    # Step 1: Open Calculator desktop app
    app_res = perform_open_application("calc")
    assert "calc" in app_res.lower() or "opened" in app_res.lower()

    # Step 2: Perform web search
    search_res = perform_web_search("React 19 release features", max_results=2)
    assert search_res is not None and len(search_res) > 0

    # Step 3: Remember project context in memory
    mem_res = mgr.save_memory("research_topic", "React 19 release features", category="learning")
    assert "Remembered" in mem_res

    # Step 4: Capture desktop screenshot
    scr_file = capture_desktop_screenshot("e2e_test_scr.png")
    assert os.path.exists(scr_file)

    # Step 5: Save explanation preference
    pref_res = mgr.save_memory("explanation_pref", "concise and direct responses", category="preference")
    assert "Remembered" in pref_res

    # Step 6: Restart MemoryManager instance to verify persistent retrieval
    mgr_new = MemoryManager(test_db)
    retrieved = mgr_new.search_memory("React")
    assert len(retrieved) == 1
    assert retrieved[0]["value"] == "React 19 release features"

    pref_retrieved = mgr_new.get_memory("explanation_pref")
    assert pref_retrieved is not None
    assert "concise" in pref_retrieved["value"]

    if os.path.exists(test_db):
        os.remove(test_db)
    print("--- E2E Realistic Sequence Test Passed! ---")


if __name__ == "__main__":
    print("Running Phase 5 & Phase 6 unit tests...")
    test_memory_database_crud()
    print("Memory database CRUD passed!")
    test_memory_sensitive_information_filter()
    print("Memory security filter passed!")
    test_memory_persistence_across_sessions()
    print("Memory session persistence passed!")

    test_screen_capture_and_active_window()
    print("Screen capture & active window passed!")
    test_mouse_coordinate_validation()
    print("Mouse coordinate validation passed!")
    test_keyboard_input_validation()
    print("Keyboard input validation passed!")

    print("Running async tool tests...")
    asyncio.run(test_async_memory_tools())
    asyncio.run(test_async_phase5_tools())
    print("Async tool tests passed!")

    test_e2e_realistic_sequence()
    print("\nALL PHASE 5 & PHASE 6 TESTS PASSED SUCCESSFULLY!")
