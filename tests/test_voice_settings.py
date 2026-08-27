"""
Unit & Integration Test Suite for LIA Voice Settings System
Covers Female Voice Defaults, Custom Voice Options, Voice Tools, Intent Classification, and Mobile API.
"""

import pytest
import urllib.request
import json
import time
from voice.voice_config import get_voice_manager, AVAILABLE_VOICES
from tools.voice_tools import (
    perform_get_voice_settings,
    perform_change_voice_setting,
    get_voice_settings,
    change_voice_setting
)
from brain.orchestrator import LIAOrchestrator, IntentType
from mobile.server import run_mobile_server


def test_female_voice_default():
    """Verify that female voice (Aoede) is the default configuration."""
    voice_mgr = get_voice_manager()
    # Reset to default female
    voice_mgr.set_voice_type("female")
    
    curr = voice_mgr.get_current_voice()
    assert curr["type"] == "female"
    assert curr["gender"] == "Female"
    assert curr["voice_id"] == "Aoede"
    assert curr["is_default"] is True
    assert "Tamil" in curr["language_support"]


def test_voice_settings_updates():
    """Verify switching voices, speaking rate, and pitch."""
    voice_mgr = get_voice_manager()

    # Switch to female_calm
    calm = voice_mgr.set_voice_type("female_calm")
    assert calm["type"] == "female_calm"
    assert calm["gender"] == "Female"
    assert calm["voice_id"] == "Kore"
    assert calm["is_default"] is False

    # Update speaking rate and pitch
    custom_settings = voice_mgr.update_voice_settings(
        voice_type="female",
        speaking_rate="1.2",
        pitch="0.5"
    )
    assert custom_settings["type"] == "female"
    assert custom_settings["speaking_rate"] == "1.2"
    assert custom_settings["pitch"] == "0.5"
    assert custom_settings["is_default"] is True


@pytest.mark.asyncio
async def test_voice_tools_functions():
    """Verify helper functions and LLM tools return formatted strings."""
    # Reset to default
    perform_change_voice_setting(voice_type="female", speaking_rate="1.0", pitch="0.0")

    # Test get_voice_settings tool
    info_str = await get_voice_settings()
    assert "LIA Voice Settings" in info_str
    assert "Aoede" in info_str
    assert "Female" in info_str

    # Test change_voice_setting tool
    change_str = await change_voice_setting(voice_type="female_warm", speaking_rate="1.1")
    assert "Voice setting updated successfully" in change_str
    assert "Female" in change_str



def test_orchestrator_voice_intent_routing():
    """Verify orchestrator correctly classifies voice setting prompts."""
    orchestrator = LIAOrchestrator()

    intent1 = orchestrator.classify_intent("Change voice to female")
    assert intent1["primary_intent"] == IntentType.VOICE_ACTION

    intent2 = orchestrator.classify_intent("LIA voice settings show")
    assert intent2["primary_intent"] == IntentType.VOICE_ACTION

    intent3 = orchestrator.classify_intent("Use female voice default")
    assert intent3["primary_intent"] == IntentType.VOICE_ACTION


def test_mobile_api_voice_endpoint():
    """Verify mobile HTTP server voice endpoint (GET & POST)."""
    server = run_mobile_server(port=8092, daemon=True)
    time.sleep(0.5)

    base_url = "http://localhost:8092/api/mobile/voice"

    # Test GET /api/mobile/voice
    req = urllib.request.urlopen(base_url)
    res_data = json.loads(req.read().decode("utf-8"))
    assert res_data["status"] == "success"
    assert "voice" in res_data
    assert res_data["voice"]["gender"] == "Female"

    # Test POST /api/mobile/voice
    post_data = json.dumps({"voice_type": "female", "speaking_rate": "1.0"}).encode("utf-8")
    post_req = urllib.request.Request(base_url, data=post_data, headers={"Content-Type": "application/json"}, method="POST")
    res_post = json.loads(urllib.request.urlopen(post_req).read().decode("utf-8"))
    assert res_post["status"] == "success"
    assert res_post["voice"]["type"] == "female"
    assert res_post["voice"]["voice_id"] == "Aoede"
