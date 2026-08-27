"""
Tools Package for LIA Agent (JARVIS Experience Expansion)
Exports all function tools for Web Intelligence, Desktop & Application Control, Window Management,
Browser Automation, Media & Music Playback, WhatsApp Integration, Calling & Contacts, OS Notifications,
Email Workflows, Safe File Management, System Telemetry, Screen Vision, Mouse & Keyboard Control,
Mobile Tools, Long-Term Memory, News Service, Reminders, Calendar, JARVIS Modes, and Desktop Startup.
"""

from tools.web_search import web_search, perform_web_search
from tools.desktop import open_application, close_application, open_folder, manage_window
from tools.browser import open_website
from tools.browser_automation import open_url, search_google, navigate_browser
from tools.system import get_system_information
from tools.screen import take_screenshot, analyze_screen, get_active_application
from tools.mouse import move_mouse, click_mouse, double_click_mouse, right_click_mouse
from tools.keyboard import type_text, press_key, press_hotkey
from tools.memory_tools import (
    remember_information,
    recall_memory,
    list_all_memories,
    forget_memory,
)
from tools.mobile import (
    get_mobile_status,
    send_mobile_notification,
    get_device_list,
    route_device_command,
)
from tools.media import play_music, control_media
from tools.whatsapp import open_whatsapp, prepare_whatsapp_message, send_whatsapp_message
from tools.contacts_calling import find_contact, prepare_phone_call
from tools.notifications import read_notifications, get_latest_notification
from tools.email_tools import open_email_client, search_emails, draft_email, send_email
from tools.files import find_file, open_file, create_folder, manage_file

# JARVIS Expansion Tools
from tools.news import get_news
from tools.reminders import create_reminder, get_reminders, cancel_reminder
from tools.calendar_tools import get_calendar_events, add_calendar_event, delete_calendar_event
from brain.modes import activate_jarvis_mode
from tools.startup import configure_desktop_startup
from tools.voice_tools import get_voice_settings, change_voice_setting, perform_get_voice_settings, perform_change_voice_setting

# Complete list of all function tools registered with LIA Agent
ALL_LIA_TOOLS = [
    web_search,
    open_application,
    close_application,
    open_folder,
    manage_window,
    open_website,
    open_url,
    search_google,
    navigate_browser,
    get_system_information,
    take_screenshot,
    analyze_screen,
    get_active_application,
    move_mouse,
    click_mouse,
    double_click_mouse,
    right_click_mouse,
    type_text,
    press_key,
    press_hotkey,
    remember_information,
    recall_memory,
    list_all_memories,
    forget_memory,
    get_mobile_status,
    send_mobile_notification,
    get_device_list,
    route_device_command,
    play_music,
    control_media,
    open_whatsapp,
    prepare_whatsapp_message,
    send_whatsapp_message,
    find_contact,
    prepare_phone_call,
    read_notifications,
    get_latest_notification,
    open_email_client,
    search_emails,
    draft_email,
    send_email,
    find_file,
    open_file,
    create_folder,
    manage_file,
    # JARVIS Experience Expansion
    get_news,
    create_reminder,
    get_reminders,
    cancel_reminder,
    get_calendar_events,
    add_calendar_event,
    delete_calendar_event,
    activate_jarvis_mode,
    configure_desktop_startup,
    get_voice_settings,
    change_voice_setting,
]

__all__ = [
    "web_search",
    "perform_web_search",
    "open_application",
    "close_application",
    "open_folder",
    "manage_window",
    "open_website",
    "open_url",
    "search_google",
    "navigate_browser",
    "get_system_information",
    "take_screenshot",
    "analyze_screen",
    "get_active_application",
    "move_mouse",
    "click_mouse",
    "double_click_mouse",
    "right_click_mouse",
    "type_text",
    "press_key",
    "press_hotkey",
    "remember_information",
    "recall_memory",
    "list_all_memories",
    "forget_memory",
    "get_mobile_status",
    "send_mobile_notification",
    "get_device_list",
    "route_device_command",
    "play_music",
    "control_media",
    "open_whatsapp",
    "prepare_whatsapp_message",
    "send_whatsapp_message",
    "find_contact",
    "prepare_phone_call",
    "read_notifications",
    "get_latest_notification",
    "open_email_client",
    "search_emails",
    "draft_email",
    "send_email",
    "find_file",
    "open_file",
    "create_folder",
    "manage_file",
    "get_news",
    "create_reminder",
    "get_reminders",
    "cancel_reminder",
    "get_calendar_events",
    "add_calendar_event",
    "delete_calendar_event",
    "activate_jarvis_mode",
    "configure_desktop_startup",
    "get_voice_settings",
    "change_voice_setting",
    "perform_get_voice_settings",
    "perform_change_voice_setting",
    "ALL_LIA_TOOLS",
]

