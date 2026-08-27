"""
Comprehensive Automated Test Suite for LIA Ultimate Capability Expansion
Validates Application Registry, Google & Browser Automation, Real-Time News, Media Controls,
WhatsApp Integration, Calling & Contacts, OS Notifications, Email Workflows, File Control,
Window Management, JARVIS Multi-step Tasks, and Security Confirmation Safeguards.
"""

import os
import pytest
import asyncio
from tools.desktop import open_application, perform_open_application, manage_window, perform_window_state
from tools.browser_automation import open_url, search_google, navigate_browser, perform_search_google
from tools.web_search import web_search, perform_web_search
from tools.media import play_music, control_media, perform_play_music, perform_control_media
from tools.whatsapp import open_whatsapp, prepare_whatsapp_message, send_whatsapp_message, perform_prepare_whatsapp_message
from tools.contacts_calling import find_contact, prepare_phone_call, perform_find_contact
from tools.notifications import read_notifications, get_latest_notification, perform_read_notifications
from tools.email_tools import open_email_client, search_emails, draft_email, send_email, perform_draft_email
from tools.files import find_file, create_folder, perform_create_folder, perform_find_file
from brain.orchestrator import LIAOrchestrator, IntentType


@pytest.mark.asyncio
async def test_application_registry():
    """Test launching allowed applications from expanded registry."""
    res_chrome = perform_open_application("chrome")
    assert "Successfully" in res_chrome or "Chrome" in res_chrome

    res_wa = perform_open_application("whatsapp")
    assert "Successfully" in res_wa or "WhatsApp" in res_wa

    res_spot = perform_open_application("spotify")
    assert "Successfully" in res_spot or "Spotify" in res_spot

    res_calc = perform_open_application("calc")
    assert "Successfully" in res_calc or "Calc" in res_calc


@pytest.mark.asyncio
async def test_google_and_browser_automation():
    """Test Google search, URL opening, and browser navigation."""
    res_g = perform_search_google("today's AI news")
    assert "Opened" in res_g or "browser" in res_g.lower()

    res_nav = await navigate_browser("refresh")
    assert "Refreshed" in res_nav


@pytest.mark.asyncio
async def test_realtime_news_categories():
    """Test web intelligence on temporal queries and category news."""
    res_news = perform_web_search("today's technology news")
    assert isinstance(res_news, str) and len(res_news) > 20

    res_jobs = perform_web_search("latest MERN jobs")
    assert isinstance(res_jobs, str) and len(res_jobs) > 20


@pytest.mark.asyncio
async def test_media_and_music():
    """Test music search and media playback controls."""
    res_play = perform_play_music("Tamil songs", platform="youtube")
    assert "YouTube" in res_play

    res_vol = perform_control_media("volume up")
    assert "Increased" in res_vol or "volume" in res_vol.lower()


@pytest.mark.asyncio
async def test_whatsapp_integration():
    """Test WhatsApp opening, message drafting, and confirmation safeguards."""
    res_prep = perform_prepare_whatsapp_message("Arun", "Hi Arun, I'll call you later.")
    assert "WhatsApp" in res_prep
    assert "Arun" in res_prep

    # Test safety guard without user confirmation
    res_unconfirmed = await send_whatsapp_message("Arun", "Hi Arun", user_confirmed=False)
    assert "SAFETY CONFIRMATION REQUIRED" in res_unconfirmed

    # Test with user confirmation
    res_confirmed = await send_whatsapp_message("Arun", "Hi Arun", user_confirmed=True)
    assert "Confirmed" in res_confirmed or "sent" in res_confirmed.lower()


@pytest.mark.asyncio
async def test_contacts_and_calling():
    """Test contact lookup and phone call preparation."""
    contact = perform_find_contact("Arun")
    assert contact["status"] == "success"
    assert "phone_number" in contact

    res_call = await prepare_phone_call("Arun")
    assert "prepared" in res_call.lower()


@pytest.mark.asyncio
async def test_notifications():
    """Test notification reading tools."""
    notifs = perform_read_notifications()
    assert notifs["status"] == "success"
    assert "notifications" in notifs

    latest = await get_latest_notification()
    assert isinstance(latest, str) and len(latest) > 5


@pytest.mark.asyncio
async def test_email_workflows():
    """Test email drafting, searching, and confirmation safeguards."""
    res_draft = perform_draft_email("arun@example.com", "Project Update", "Here is the latest update.")
    assert "Drafted" in res_draft

    # Unconfirmed send email guard
    res_unconfirmed = await send_email("arun@example.com", "Test", "Content", user_confirmed=False)
    assert "SAFETY CONFIRMATION REQUIRED" in res_unconfirmed

    # Confirmed send email
    res_confirmed = await send_email("arun@example.com", "Test", "Content", user_confirmed=True)
    assert "Confirmed" in res_confirmed or "sent" in res_confirmed.lower()


@pytest.mark.asyncio
async def test_file_control():
    """Test safe file search and folder creation."""
    res_folder = perform_create_folder("LIA_Test_Folder")
    assert "Successfully created" in res_folder or "LIA_Test_Folder" in res_folder

    # Clean up created test folder
    folder_path = os.path.expanduser("~/Documents/LIA_Test_Folder")
    if os.path.exists(folder_path):
        try:
            os.rmdir(folder_path)
        except Exception:
            pass


@pytest.mark.asyncio
async def test_multistep_jarvis_tasks():
    """Test multi-step task parsing in LIAOrchestrator."""
    orchestrator = LIAOrchestrator()

    steps1 = orchestrator.parse_multistep_task("open Google, search today's AI news, summarize the top three stories and tell me")
    assert len(steps1) >= 2

    steps2 = orchestrator.parse_multistep_task("open YouTube and play Tamil music")
    assert len(steps2) >= 2

    steps3 = orchestrator.parse_multistep_task("search today's MERN jobs and open the most relevant result")
    assert len(steps3) >= 2
