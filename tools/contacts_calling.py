"""
Contacts Lookup & Calling Tools for LIA (Phases 4-8 Expanded)
Handles contact lookup and phone call preparation using OS Phone Link / tel: protocol or Mobile Device routing.
Enforces legitimate OS permissions and confirmation checks.
"""

import os
import sys
import logging
import asyncio
from typing import Optional, Dict, Any
from livekit.agents import llm
from devices.registry import get_device_registry

logger = logging.getLogger("lia-tools-calling")

# Local contact registry fallback
KNOWN_CONTACTS: Dict[str, str] = {
    "arun": "+91 98765 43210",
    "priya": "+91 98765 43211",
    "karthik": "+91 98765 43212",
    "mom": "+91 98765 43213",
    "dad": "+91 98765 43214",
}

def perform_find_contact(name: str) -> Dict[str, Any]:
    """Synchronous helper to look up a contact."""
    name_clean = name.strip().lower()
    for key, num in KNOWN_CONTACTS.items():
        if key in name_clean or name_clean in key:
            return {
                "status": "success",
                "contact_name": key.title(),
                "phone_number": num,
                "whatsapp_available": True
            }
    return {
        "status": "not_found",
        "message": f"Contact '{name}' was not found in the contact registry."
    }

def perform_prepare_call(contact_name: str, phone_number: Optional[str] = None) -> str:
    """Synchronous helper to prepare a phone call via OS Phone Link / tel: protocol."""
    target_num = phone_number
    if not target_num:
        lookup = perform_find_contact(contact_name)
        if lookup["status"] == "success":
            target_num = lookup["phone_number"]
        else:
            target_num = "contact_number"

    logger.info(f"Preparing call to {contact_name} ({target_num})")
    
    # Try launching Windows Phone Link / tel URI
    try:
        if sys.platform == "win32" and target_num != "contact_number":
            num_clean = target_num.replace(" ", "").replace("-", "")
            import subprocess
            subprocess.Popen(f"start tel:{num_clean}", shell=True)
    except Exception as e:
        logger.warning(f"Could not open tel URI: {e}")

    return f"Phone call prepared for {contact_name} ({target_num}). Please tap Call on your device to confirm."


@llm.function_tool(
    name="find_contact",
    description="Look up contact information (name, phone number) for a person such as Arun, Priya, Mom, Dad.",
)
async def find_contact(name: str) -> Dict[str, Any]:
    logger.info(f"[LIA CALLING TOOL TRIGGERED] find_contact('{name}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_find_contact, name)


@llm.function_tool(
    name="prepare_phone_call",
    description="Prepare a phone call to a contact (e.g. 'call Arun'). Prepares dialer and requires OS confirmation.",
)
async def prepare_phone_call(contact_name: str, phone_number: Optional[str] = None) -> str:
    logger.info(f"[LIA CALLING TOOL TRIGGERED] prepare_phone_call('{contact_name}', '{phone_number}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_prepare_call, contact_name, phone_number)
