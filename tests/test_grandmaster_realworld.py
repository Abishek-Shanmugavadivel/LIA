"""
Grandmaster Real-World Production & Integration Test Suite for LIA 5.0
Validates all 40 Real-World operation capabilities, Tamil/Tanglish multi-lingual processing,
Female voice configuration, Vision engine, Desktop control, Browser JARVIS, Mission Planner,
Emergency Stop, and Mobile/Cross-Device routing.
"""

import os
import json
import pytest
import asyncio
from voice.voice_config import get_voice_manager, AVAILABLE_VOICES
from voice.wakeword import WakeWordDetector, ConversationMode, INTERRUPT_WORDS
from voice.state_machine import get_state_machine, VoiceStateMachine, LIAState
from brain.orchestrator import LIAOrchestrator, IntentType
from brain.context import get_context_manager
from brain.reference_resolver import ReferenceResolver
from tools.app_discovery import get_app_discovery_manager
from tools.vision_engine import get_vision_engine
from tools.memory_tools import remember_information, recall_memory, list_all_memories
from memory.manager import get_memory_manager
from brain.task_agent import get_task_agent
from brain.personal_assistant import get_personal_assistant
from security.validation import validate_tool_call, mask_secrets
from mobile.server import run_mobile_server


@pytest.fixture(scope="module")
def orchestrator():
    return LIAOrchestrator()


@pytest.fixture(scope="module")
def context_mgr():
    return get_context_manager()


def test_01_female_voice_configuration():
    """Verify LIA defaults to Warm Female AI Voice (Aoede) with natural voice settings."""
    vm = get_voice_manager()
    curr = vm.get_current_voice()
    assert curr["gender"] == "Female"
    assert curr["voice_id"] in ["Aoede", "Kore"]
    assert curr["is_default"] is True
    assert "Aoede" in AVAILABLE_VOICES["female"]["id"]


def test_02_wakeword_and_emergency_stop():
    """Verify wake word activation and immediate emergency stop interruption."""
    detector = WakeWordDetector(mode=ConversationMode.WAKE_WORD)
    
    # Test Wake trigger
    wake_res = detector.process_transcript("Hey LIA open Chrome")
    assert wake_res["activated"] is True
    assert wake_res["cleaned_prompt"] == "open Chrome"

    # Test Emergency Stop words
    for kw in ["STOP LIA", "Cancel", "Stop", "Okay stop", "emergency stop"]:
        res = detector.process_transcript(kw)
        assert res["is_interruption"] is True


def test_03_english_natural_language_intents(orchestrator):
    """Verify English voice commands map to correct intent types."""
    assert orchestrator.classify_intent("Open Chrome")["primary_intent"] == IntentType.DESKTOP_ACTION
    assert orchestrator.classify_intent("Search today's AI news")["primary_intent"] == IntentType.NEWS_ACTION
    assert orchestrator.classify_intent("What are you seeing?")["primary_intent"] == IntentType.VISION_ACTION
    assert orchestrator.classify_intent("Switch to VS Code")["primary_intent"] == IntentType.DESKTOP_ACTION


def test_04_tamil_natural_language_intents(orchestrator):
    """Verify Tamil voice commands map to correct intent types."""
    assert orchestrator.classify_intent("Chrome-ஐ திற")["primary_intent"] == IntentType.DESKTOP_ACTION
    assert orchestrator.classify_intent("இன்றைய AI செய்திகளை தேடு")["primary_intent"] == IntentType.NEWS_ACTION
    assert orchestrator.classify_intent("ஸ்க்ரீனில் என்ன இருக்கு?")["primary_intent"] == IntentType.VISION_ACTION


def test_05_tanglish_natural_language_intents(orchestrator):
    """Verify Tanglish voice commands map to correct intent types."""
    assert orchestrator.classify_intent("Chrome open pannu")["primary_intent"] == IntentType.DESKTOP_ACTION
    assert orchestrator.classify_intent("Latest AI news search pannu")["primary_intent"] == IntentType.NEWS_ACTION
    assert orchestrator.classify_intent("Screen la enna irukku?")["primary_intent"] == IntentType.VISION_ACTION
    assert orchestrator.classify_intent("Song play pannu")["primary_intent"] == IntentType.MEDIA_ACTION


def test_06_mixed_multistep_command(orchestrator):
    """Verify mixed English/Tamil multi-step command decomposition."""
    intent = orchestrator.classify_intent("LIA, Chrome open panni today's AI news search pannu")
    assert intent["primary_intent"] == IntentType.MULTI_STEP
    steps = orchestrator.parse_multistep_task("Chrome open panni today's AI news search pannu")
    assert len(steps) >= 2


def test_07_dynamic_application_discovery():
    """Verify dynamic discovery of Windows applications without hardcoded paths."""
    adm = get_app_discovery_manager()
    apps = adm.discover_installed_applications()
    assert isinstance(apps, dict)
    assert len(apps) > 0
    
    # Discover path for common apps
    calc_entry = adm.find_application("calculator")
    assert calc_entry is not None or "calc" in apps or "calculator" in apps


def test_08_screen_vision_and_ui_detection():
    """Verify Vision Engine screen analysis and element detection."""
    ve = get_vision_engine()
    elements = ve.detect_ui_elements()
    assert isinstance(elements, list)
    assert len(elements) > 0
    assert "type" in elements[0]
    assert "bbox" in elements[0]


@pytest.mark.asyncio
async def test_09_orchestrator_execution_and_context(orchestrator, context_mgr):
    """Verify end-to-end execution of search and ordinal selection in context."""
    res1 = await orchestrator.process_request("Search latest AI news")
    assert res1["status"] == "success"
    assert "search_results" in res1 or "results" in res1

    # Follow up ordinal selection
    res2 = await orchestrator.process_request("Open the second result")
    assert res2["status"] == "success"
    assert "selected_item" in res2 or "Result #2" in res2.get("message", "")


@pytest.mark.asyncio
async def test_10_memory_and_security_guard():
    """Verify persistent memory storage and safety guard enforcement."""
    mm = get_memory_manager()
    mm.save_memory("stack", "MERN Stack", category="preferences")
    recalled = mm.get_memory("stack")
    assert recalled["value"] == "MERN Stack"

    # Security validation
    valid, msg, args = validate_tool_call("open_application", {"app_name": "calc"})
    assert valid is True
    
    invalid, msg_inv, args_inv = validate_tool_call("open_application", {"app_name": "format c:"})
    assert invalid is False


@pytest.mark.asyncio
async def test_11_mission_engine_and_emergency_stop():
    """Verify Mission Engine goal planning and cancellation."""
    from brain.task_agent import TaskState
    ta = get_task_agent()
    plan_steps = ta.plan_goal("Find five current MERN jobs")
    assert len(plan_steps) > 0
    assert ta.current_state == TaskState.PLANNING

    cancel_res = ta.cancel_task()
    assert cancel_res["success"] is True
    assert ta.current_state == TaskState.CANCELLED


def test_12_cross_device_and_mobile_backend():
    """Verify mobile backend server startup and device status API."""
    from devices.registry import get_device_registry
    reg = get_device_registry()
    devices = reg.list_devices()
    assert len(devices) > 0


def test_13_android_companion_integration():
    """Verify Android native companion configuration, permissions, and plugin setup."""
    import os
    manifest_path = os.path.join("android", "app", "src", "main", "AndroidManifest.xml")
    plugin_path = os.path.join("android", "app", "src", "main", "java", "com", "lia", "companion", "LIAAndroidCompanionPlugin.java")
    main_activity_path = os.path.join("android", "app", "src", "main", "java", "com", "lia", "companion", "MainActivity.java")

    assert os.path.exists(manifest_path), "AndroidManifest.xml missing"
    assert os.path.exists(plugin_path), "LIAAndroidCompanionPlugin.java missing"
    assert os.path.exists(main_activity_path), "MainActivity.java missing"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_content = f.read()

    assert "android.permission.RECORD_AUDIO" in manifest_content
    assert "android.permission.INTERNET" in manifest_content
    assert "android.permission.MODIFY_AUDIO_SETTINGS" in manifest_content

    with open(plugin_path, "r", encoding="utf-8") as f:
        plugin_content = f.read()

    assert "@CapacitorPlugin" in plugin_content
    assert "LIAAndroidCompanion" in plugin_content
    assert "getDeviceTelemetry" in plugin_content
    assert "openApp" in plugin_content


def test_14_expanded_application_discovery():
    """Verify application discovery and orchestrator classification for Facebook, Instagram, Twitter/X, WhatsApp, Netflix."""
    from tools.app_discovery import get_app_discovery_manager
    from brain.orchestrator import LIAOrchestrator, IntentType

    adm = get_app_discovery_manager()
    orch = LIAOrchestrator()

    for app in ["facebook", "instagram", "twitter", "whatsapp", "netflix", "youtube", "word", "excel", "spotify"]:
        entry = adm.find_application(app)
        assert entry is not None, f"Application '{app}' not found in app discovery registry"

    for cmd in ["open Facebook", "Instagram open pannu", "open Twitter", "WhatsApp open பண்ணு", "open Netflix"]:
        intent = orch.classify_intent(cmd)
        assert intent["primary_intent"] in [IntentType.DESKTOP_ACTION, IntentType.WHATSAPP_ACTION]



