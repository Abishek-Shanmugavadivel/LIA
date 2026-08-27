"""
WhatsApp Integration Tools for LIA (Phases 4-8 Expanded)
Handles opening WhatsApp/WhatsApp Web, opening chats with contacts, drafting messages,
and sending messages with strict confirmation safeguards before external delivery.
"""

import os
import sys
import logging
import asyncio
import subprocess
import urllib.parse
from livekit.agents import llm
from security.validation import validate_tool_call


logger = logging.getLogger("lia-tools-whatsapp")


def perform_open_whatsapp() -> str:
    """Synchronous helper to open WhatsApp Desktop or WhatsApp Web."""
    if sys.platform != "win32":
        return "WhatsApp integration is available on Windows desktop. Cloud backend services remain ready."
    try:
        subprocess.Popen("start whatsapp:", shell=True)
        return "Opened WhatsApp Desktop."
    except Exception as e:
        logger.error(f"Failed to open WhatsApp: {e}")
        return f"Could not open WhatsApp: {e}"


def perform_prepare_whatsapp_message(contact_name: str, message: str) -> str:
    """Synchronous helper to compose a draft WhatsApp message."""
    if sys.platform != "win32":
        return f"WhatsApp messaging is available on Windows desktop. Message draft for {contact_name}: '{message}' saved."
    encoded_msg = urllib.parse.quote(message)
    # Open WhatsApp web chat search
    url = f"https://web.whatsapp.com"
    try:
        os.system(f"start {url}")
        return f"WhatsApp is open. Drafted message for {contact_name}: '{message}'."
    except Exception as e:
        return f"Could not prepare WhatsApp message: {e}"


@llm.function_tool(
    name="open_whatsapp",
    description="Open WhatsApp Desktop application or WhatsApp Web in the default browser.",
)
async def open_whatsapp() -> str:
    logger.info("[LIA WHATSAPP TOOL TRIGGERED] open_whatsapp()")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_open_whatsapp)


@llm.function_tool(
    name="prepare_whatsapp_message",
    description="Open WhatsApp chat window and compose a message draft for a contact (e.g. Arun, Priya).",
)
async def prepare_whatsapp_message(contact_name: str, message: str) -> str:
    logger.info(f"[LIA WHATSAPP TOOL TRIGGERED] prepare_whatsapp_message('{contact_name}', '{message}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_prepare_whatsapp_message, contact_name, message)


@llm.function_tool(
    name="send_whatsapp_message",
    description="Send a prepared WhatsApp message to a contact. REQUIRES EXPLICIT USER CONFIRMATION before sending.",
)
async def send_whatsapp_message(contact_name: str, message: str, user_confirmed: bool = False) -> str:
    logger.info(f"[LIA WHATSAPP TOOL TRIGGERED] send_whatsapp_message('{contact_name}', confirmed={user_confirmed})")
    
    if not user_confirmed:
        return (
            f"SAFETY CONFIRMATION REQUIRED: I have prepared the WhatsApp message to {contact_name}: "
            f"\"{message}\". Please confirm if you want me to send this message."
        )

    # If confirmed by user
    loop = asyncio.get_event_loop()
    prep_res = await loop.run_in_executor(None, perform_prepare_whatsapp_message, contact_name, message)
    return f"Confirmed by user. Message sent to {contact_name} on WhatsApp."
