"""
Automated Integration & Unit Test Suite for LIA JARVIS Experience Expansion (Phase 9)
Covers Voice Settings (Female/Male/Custom), News Service, Reminders, Calendar, JARVIS Modes,
Desktop Startup, Multilingual Tanglish Intent Routing, Mobile Endpoints, and Confirmation Safety Guards.
"""

import pytest
import os
import sys
import json
import urllib.request
import threading
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from voice.voice_config import get_voice_manager, AVAILABLE_VOICES
from tools.news import perform_get_news
from tools.reminders import perform_create_reminder, perform_get_reminders, perform_cancel_reminder
from tools.calendar_tools import perform_get_calendar_events, perform_add_calendar_event, perform_delete_calendar_event
from brain.modes import perform_activate_jarvis_mode, get_active_mode
from tools.startup import perform_configure_startup
from brain.orchestrator import LIAOrchestrator, IntentType
from tools.whatsapp import send_whatsapp_message
from tools.contacts_calling import perform_prepare_call
from mobile.server import run_mobile_server


def test_female_voice_configuration_default():
    voice_mgr = get_voice_manager()
    curr = voice_mgr.get_current_voice()
    assert curr["type"] in ["female", "male", "custom"]
    
    # Set to female explicit default
    updated = voice_mgr.set_voice_type("female")
    assert updated["type"] == "female"
    assert updated["voice_id"] == AVAILABLE_VOICES["female"]["id"]
    assert "Tamil" in updated["language_support"]


def test_voice_configuration_switching():
    voice_mgr = get_voice_manager()
    
    # Switch to male
    male_voice = voice_mgr.set_voice_type("male")
    assert male_voice["type"] == "male"
    assert male_voice["voice_id"] == AVAILABLE_VOICES["male"]["id"]

    # Switch back to female default
    female_voice = voice_mgr.set_voice_type("female")
    assert female_voice["type"] == "female"


def test_news_service_tool():
    res_tech = perform_get_news(topic_or_category="technology", timeframe="latest")
    assert "News Highlights" in res_tech or "No latest news" in res_tech or "technology" in res_tech
    
    res_ai = perform_get_news(topic_or_category="AI", timeframe="today")
    assert "News Highlights" in res_ai or "No latest news" in res_ai or "AI" in res_ai


def test_reminders_crud():
    # Create reminder
    rem_msg = perform_create_reminder(title="Team Standup", datetime_str="6 PM")
    assert "created" in rem_msg
    
    # Get reminders
    list_msg = perform_get_reminders(filter_status="pending")
    assert "Team Standup" in list_msg

    # Extract ID and cancel (ID format: Reminder #1)
    if "#" in rem_msg:
        rem_id = int(rem_msg.split("#")[1].split(" ")[0])
        cancel_msg = perform_cancel_reminder(rem_id)
        assert "cancelled" in cancel_msg


def test_calendar_crud():
    # Add meeting
    add_msg = perform_add_calendar_event(title="Architecture Review", date_str="tomorrow", time_str="3:00 PM")
    assert "scheduled" in add_msg

    # Get schedule
    cal_msg = perform_get_calendar_events(date_str="tomorrow")
    assert "Architecture Review" in cal_msg


def test_jarvis_modes_activation():
    coding_res = perform_activate_jarvis_mode("coding")
    assert "Coding Mode active" in coding_res
    assert "Coding Mode" in get_active_mode()

    study_res = perform_activate_jarvis_mode("study")
    assert "Study Mode active" in study_res


def test_desktop_startup_configuration():
    # Configure startup (should safely handle non-Windows or return status string)
    res = perform_configure_startup(enable=False)
    assert isinstance(res, str)


def test_multilingual_tanglish_intent_routing():
    orchestrator = LIAOrchestrator()

    # Tanglish open google
    intent1 = orchestrator.classify_intent("LIA Google open pannu")
    assert intent1["primary_intent"] == IntentType.DESKTOP_ACTION

    # Tanglish play music
    intent2 = orchestrator.classify_intent("LIA Tamil song play pannu")
    assert intent2["primary_intent"] == IntentType.MEDIA_ACTION

    # Tanglish AI news
    intent3 = orchestrator.classify_intent("LIA latest AI news sollu")
    assert intent3["primary_intent"] == IntentType.NEWS_ACTION

    # Mode action
    intent4 = orchestrator.classify_intent("Start coding mode")
    assert intent4["primary_intent"] == IntentType.MODE_ACTION


@pytest.mark.asyncio
async def test_whatsapp_confirmation_guard():
    # Attempt sending without confirmation -> should return confirmation request
    res = await send_whatsapp_message(contact_name="Arun", message="Hello Arun", user_confirmed=False)
    assert "SAFETY CONFIRMATION REQUIRED" in res


def test_mobile_server_jarvis_api_endpoints():
    server = run_mobile_server(port=8089, daemon=True)
    time.sleep(0.5)

    base_url = "http://localhost:8089"

    # Test /api/mobile/news
    req_news = urllib.request.urlopen(f"{base_url}/api/mobile/news", timeout=8)
    data_news = json.loads(req_news.read().decode("utf-8"))
    assert data_news["status"] == "success"

    # Test /api/mobile/voice
    req_voice = urllib.request.urlopen(f"{base_url}/api/mobile/voice", timeout=8)
    data_voice = json.loads(req_voice.read().decode("utf-8"))
    assert data_voice["status"] == "success"

    # Test /api/mobile/mode
    req_mode = urllib.request.urlopen(f"{base_url}/api/mobile/mode", timeout=8)
    data_mode = json.loads(req_mode.read().decode("utf-8"))
    assert data_mode["status"] == "success"

    # Test GET / (index.html serving with LiveKit client)
    req_index = urllib.request.urlopen(f"{base_url}/", timeout=8)
    html_content = req_index.read().decode("utf-8")
    assert "livekit-client.umd.min.js" in html_content
    assert "connectToLIA" in html_content

    # Test GET/POST /api/mobile/token
    token_req = urllib.request.Request(
        f"{base_url}/api/mobile/token",
        data=json.dumps({"identity": "test_mobile_user", "room": "lia_default_room"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    req_token = urllib.request.urlopen(token_req, timeout=8)
    data_token = json.loads(req_token.read().decode("utf-8"))
    assert data_token["status"] == "success"
    assert "token" in data_token
    assert "url" in data_token
    assert data_token["room"] == "lia_default_room"
