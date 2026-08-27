"""
LIA 5.0 Tools Package

Cross-platform tool registry.

Windows:
    Full JARVIS desktop capabilities are enabled.

Linux / Render:
    Cloud-safe tools are loaded.
    Desktop GUI tools are intentionally not imported because
    Render has no Windows desktop or DISPLAY server.
"""

import sys
import platform
import logging

logger = logging.getLogger("lia-tools")

IS_WINDOWS = sys.platform == "win32"


# =========================================================
# CLOUD-SAFE TOOLS
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
# WINDOWS-ONLY DESKTOP / GUI TOOLS
# =========================================================

if IS_WINDOWS:

    logger.info(
        "Windows detected. Loading full desktop JARVIS tools."
    )

    # -----------------------------------------------------
    # Desktop
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
    # Media
    # -----------------------------------------------------

    from tools.media import (
        play_music,
        control_media,
    )

    # -----------------------------------------------------
    # WhatsApp
    # -----------------------------------------------------

    from tools.whatsapp import (
        open_whatsapp,
        prepare_whatsapp_message,
        send_whatsapp_message,
    )

    # -----------------------------------------------------
    # Contacts / Calling
    # -----------------------------------------------------

    from tools.contacts_calling import (
        find_contact,
        prepare_phone_call,
    )

    # -----------------------------------------------------
    # Startup
    # -----------------------------------------------------

    from tools.startup import (
        configure_desktop_startup,
    )

else:

    logger.info(
        "Non-Windows platform detected (%s). "
        "Desktop GUI tools disabled.",
        platform.system(),
    )


# =========================================================
# TOOL REGISTRY
# =========================================================

ALL_LIA_TOOLS = [

    # -----------------------------------------------------
    # Web
    # -----------------------------------------------------

    web_search,

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
    # News
    # -----------------------------------------------------

    get_news,

    # -----------------------------------------------------
    # Reminders
    # -----------------------------------------------------

    create_reminder,
    get_reminders,
    cancel_reminder,

    # -----------------------------------------------------
    # Calendar
    # -----------------------------------------------------

    get_calendar_events,
    add_calendar_event,
    delete_calendar_event,

    # -----------------------------------------------------
    # JARVIS Mode
    # -----------------------------------------------------

    activate_jarvis_mode,

    # -----------------------------------------------------
    # Voice
    # -----------------------------------------------------

    get_voice_settings,
    change_voice_setting,
]


# =========================================================
# WINDOWS TOOL REGISTRATION
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

            # Screen
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

            # Media
            play_music,
            control_media,

            # WhatsApp
            open_whatsapp,
            prepare_whatsapp_message,
            send_whatsapp_message,

            # Contacts
            find_contact,
            prepare_phone_call,

            # Startup
            configure_desktop_startup,
        ]
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================

__all__ = [
    "web_search",
    "perform_web_search",

    "open_website",

    "get_system_information",

    "remember_information",
    "recall_memory",
    "list_all_memories",
    "forget_memory",

    "get_mobile_status",
    "send_mobile_notification",
    "get_device_list",
    "route_device_command",

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

    "get_voice_settings",
    "change_voice_setting",
    "perform_get_voice_settings",
    "perform_change_voice_setting",

    "ALL_LIA_TOOLS",
]


# =========================================================
# WINDOWS EXPORTS
# =========================================================

if IS_WINDOWS:

    __all__.extend(
        [

            "open_application",
            "close_application",
            "open_folder",
            "manage_window",

            "open_url",
            "search_google",
            "navigate_browser",

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

            "play_music",
            "control_media",

            "open_whatsapp",
            "prepare_whatsapp_message",
            "send_whatsapp_message",

            "find_contact",
            "prepare_phone_call",

            "configure_desktop_startup",
        ]
    )


# =========================================================
# DIAGNOSTIC
# =========================================================

logger.info(
    "LIA tools initialized | Platform=%s | Windows=%s | Tools=%d",
    platform.system(),
    IS_WINDOWS,
    len(ALL_LIA_TOOLS),
)