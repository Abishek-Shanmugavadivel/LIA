"""
LIA 5.0 Tools Package

Cross-platform tool registry.

Windows:
    Enables the complete JARVIS desktop experience:
    - Desktop/application control
    - Browser automation
    - Screen capture/vision
    - Mouse/keyboard
    - Startup management

Linux/Render:
    Enables cloud-safe tools only.
    Windows GUI tools are NOT imported, preventing failures
    caused by pyautogui, pygetwindow, DISPLAY, Win32 APIs, etc.
"""

import platform
import logging

logger = logging.getLogger("lia-tools")

IS_WINDOWS = platform.system().lower() == "windows"


# =========================================================
# SAFE / CLOUD-COMPATIBLE TOOLS
# =========================================================

from tools.web_search import (
    web_search,
    perform_web_search,
)

from tools.browser import (
    open_website,
)

from tools.system import (
    get_system_information,
)

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

from tools.media import (
    play_music,
    control_media,
)

from tools.whatsapp import (
    open_whatsapp,
    prepare_whatsapp_message,
    send_whatsapp_message,
)

from tools.contacts_calling import (
    find_contact,
    prepare_phone_call,
)

from tools.notifications import (
    read_notifications,
    get_latest_notification,
)

from tools.email_tools import (
    open_email_client,
    search_emails,
    draft_email,
    send_email,
)

from tools.files import (
    find_file,
    open_file,
    create_folder,
    manage_file,
)

from tools.news import (
    get_news,
)

from tools.reminders import (
    create_reminder,
    get_reminders,
    cancel_reminder,
)

from tools.calendar_tools import (
    get_calendar_events,
    add_calendar_event,
    delete_calendar_event,
)

from brain.modes import (
    activate_jarvis_mode,
)

from tools.voice_tools import (
    get_voice_settings,
    change_voice_setting,
    perform_get_voice_settings,
    perform_change_voice_setting,
)


# =========================================================
# WINDOWS-ONLY GUI TOOLS
# =========================================================

if IS_WINDOWS:

    logger.info(
        "Windows detected: loading full LIA desktop tools."
    )

    # -----------------------------------------------------
    # Desktop / Application Control
    # -----------------------------------------------------

    from tools.desktop import (
        open_application,
        close_application,
        open_folder,
        manage_window,
    )

    # -----------------------------------------------------
    # Browser Automation
    # -----------------------------------------------------

    from tools.browser_automation import (
        open_url,
        search_google,
        navigate_browser,
    )

    # -----------------------------------------------------
    # Screen / Vision
    # -----------------------------------------------------

    from tools.screen import (
        take_screenshot,
        analyze_screen,
        get_active_application,
    )

    # -----------------------------------------------------
    # Mouse
    # -----------------------------------------------------

    from tools.mouse import (
        move_mouse,
        click_mouse,
        double_click_mouse,
        right_click_mouse,
    )

    # -----------------------------------------------------
    # Keyboard
    # -----------------------------------------------------

    from tools.keyboard import (
        type_text,
        press_key,
        press_hotkey,
    )

    # -----------------------------------------------------
    # Desktop Startup
    # -----------------------------------------------------

    from tools.startup import (
        configure_desktop_startup,
    )

else:

    logger.info(
        "Non-Windows platform detected (%s): "
        "Windows GUI tools disabled.",
        platform.system(),
    )


# =========================================================
# TOOL REGISTRY
# =========================================================

ALL_LIA_TOOLS = [
    # -----------------------------------------------------
    # Web Intelligence
    # -----------------------------------------------------

    web_search,

    # -----------------------------------------------------
    # Browser (safe website opening)
    # -----------------------------------------------------

    open_website,

    # -----------------------------------------------------
    # System
    # -----------------------------------------------------

    get_system_information,

    # -----------------------------------------------------
    # Memory
    # -----------------------------------------------------

    remember_information,
    recall_memory,
    list_all_memories,
    forget_memory,

    # -----------------------------------------------------
    # Mobile
    # -----------------------------------------------------

    get_mobile_status,
    send_mobile_notification,
    get_device_list,
    route_device_command,

    # -----------------------------------------------------
    # Media
    # -----------------------------------------------------

    play_music,
    control_media,

    # -----------------------------------------------------
    # WhatsApp
    # -----------------------------------------------------

    open_whatsapp,
    prepare_whatsapp_message,
    send_whatsapp_message,

    # -----------------------------------------------------
    # Contacts / Calling
    # -----------------------------------------------------

    find_contact,
    prepare_phone_call,

    # -----------------------------------------------------
    # Notifications
    # -----------------------------------------------------

    read_notifications,
    get_latest_notification,

    # -----------------------------------------------------
    # Email
    # -----------------------------------------------------

    open_email_client,
    search_emails,
    draft_email,
    send_email,

    # -----------------------------------------------------
    # Files
    # -----------------------------------------------------

    find_file,
    open_file,
    create_folder,
    manage_file,

    # -----------------------------------------------------
    # JARVIS Expansion
    # -----------------------------------------------------

    get_news,

    create_reminder,
    get_reminders,
    cancel_reminder,

    get_calendar_events,
    add_calendar_event,
    delete_calendar_event,

    activate_jarvis_mode,

    # -----------------------------------------------------
    # Voice
    # -----------------------------------------------------

    get_voice_settings,
    change_voice_setting,
]


# =========================================================
# ADD WINDOWS TOOLS ONLY ON WINDOWS
# =========================================================

if IS_WINDOWS:

    ALL_LIA_TOOLS.extend(
        [
            # Desktop
            open_application,
            close_application,
            open_folder,
            manage_window,

            # Browser automation
            open_url,
            search_google,
            navigate_browser,

            # Screen / vision
            take_screenshot,
            analyze_screen,
            get_active_application,

            # Mouse
            move_mouse,
            click_mouse,
            double_click_mouse,
            right_click_mouse,

            # Keyboard
            type_text,
            press_key,
            press_hotkey,

            # Startup
            configure_desktop_startup,
        ]
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================

__all__ = [
    # -----------------------------------------------------
    # Web
    # -----------------------------------------------------

    "web_search",
    "perform_web_search",

    # -----------------------------------------------------
    # Browser
    # -----------------------------------------------------

    "open_website",

    # -----------------------------------------------------
    # System
    # -----------------------------------------------------

    "get_system_information",

    # -----------------------------------------------------
    # Memory
    # -----------------------------------------------------

    "remember_information",
    "recall_memory",
    "list_all_memories",
    "forget_memory",

    # -----------------------------------------------------
    # Mobile
    # -----------------------------------------------------

    "get_mobile_status",
    "send_mobile_notification",
    "get_device_list",
    "route_device_command",

    # -----------------------------------------------------
    # Media
    # -----------------------------------------------------

    "play_music",
    "control_media",

    # -----------------------------------------------------
    # WhatsApp
    # -----------------------------------------------------

    "open_whatsapp",
    "prepare_whatsapp_message",
    "send_whatsapp_message",

    # -----------------------------------------------------
    # Contacts / Calling
    # -----------------------------------------------------

    "find_contact",
    "prepare_phone_call",

    # -----------------------------------------------------
    # Notifications
    # -----------------------------------------------------

    "read_notifications",
    "get_latest_notification",

    # -----------------------------------------------------
    # Email
    # -----------------------------------------------------

    "open_email_client",
    "search_emails",
    "draft_email",
    "send_email",

    # -----------------------------------------------------
    # Files
    # -----------------------------------------------------

    "find_file",
    "open_file",
    "create_folder",
    "manage_file",

    # -----------------------------------------------------
    # JARVIS
    # -----------------------------------------------------

    "get_news",
    "create_reminder",
    "get_reminders",
    "cancel_reminder",

    "get_calendar_events",
    "add_calendar_event",
    "delete_calendar_event",

    "activate_jarvis_mode",

    # -----------------------------------------------------
    # Voice
    # -----------------------------------------------------

    "get_voice_settings",
    "change_voice_setting",
    "perform_get_voice_settings",
    "perform_change_voice_setting",

    # -----------------------------------------------------
    # Registry
    # -----------------------------------------------------

    "ALL_LIA_TOOLS",
]


# =========================================================
# WINDOWS EXPORTS
# =========================================================

if IS_WINDOWS:

    __all__.extend(
        [
            # Desktop
            "open_application",
            "close_application",
            "open_folder",
            "manage_window",

            # Browser automation
            "open_url",
            "search_google",
            "navigate_browser",

            # Screen
            "take_screenshot",
            "analyze_screen",
            "get_active_application",

            # Mouse
            "move_mouse",
            "click_mouse",
            "double_click_mouse",
            "right_click_mouse",

            # Keyboard
            "type_text",
            "press_key",
            "press_hotkey",

            # Startup
            "configure_desktop_startup",
        ]
    )


# =========================================================
# STARTUP DIAGNOSTIC
# =========================================================

logger.info(
    "LIA tools initialized. Platform=%s, Windows=%s, Tools=%d",
    platform.system(),
    IS_WINDOWS,
    len(ALL_LIA_TOOLS),
)