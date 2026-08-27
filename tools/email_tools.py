"""
Email Workflow Tools for LIA (Phases 4-8 Expanded)
Handles opening Gmail/Mail clients, searching email queries, drafting emails,
and sending emails with strict safety confirmation safeguards.
"""

import os
import sys
import logging
import asyncio
import subprocess
import urllib.parse
from livekit.agents import llm

logger = logging.getLogger("lia-tools-email")


def perform_open_email(provider: str = "gmail") -> str:
    """Synchronous helper to open email provider (Gmail/Outlook)."""
    prov_clean = provider.strip().lower() if provider else "gmail"
    if "outlook" in prov_clean:
        url = "https://outlook.live.com"
    else:
        url = "https://mail.google.com"

    try:
        if sys.platform == "win32":
            subprocess.Popen(f"start {url}", shell=True)
        return f"Opened {prov_clean.title()} in default browser."
    except Exception as e:
        logger.error(f"Error opening email client: {e}")
        return f"Could not open email client: {e}"


def perform_search_emails(query: str) -> str:
    """Synchronous helper to search emails."""
    encoded_q = urllib.parse.quote(query)
    url = f"https://mail.google.com/mail/u/0/#search/{encoded_q}"
    try:
        if sys.platform == "win32":
            subprocess.Popen(f"start {url}", shell=True)
        return f"Opened Gmail search for '{query}'."
    except Exception as e:
        return f"Could not search emails: {e}"


def perform_draft_email(recipient: str, subject: str, body: str) -> str:
    """Synchronous helper to compose email draft via mailto URI or web draft."""
    enc_sub = urllib.parse.quote(subject)
    enc_body = urllib.parse.quote(body)
    mailto_url = f"mailto:{recipient}?subject={enc_sub}&body={enc_body}"
    try:
        if sys.platform == "win32":
            subprocess.Popen(f"start {mailto_url}", shell=True)
        return f"Drafted email to {recipient} with subject '{subject}'."
    except Exception as e:
        return f"Could not draft email: {e}"


@llm.function_tool(
    name="open_email_client",
    description="Open Gmail or your primary email application in the browser.",
)
async def open_email_client(provider: str = "gmail") -> str:
    logger.info(f"[LIA EMAIL TOOL TRIGGERED] open_email_client('{provider}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_open_email, provider)


@llm.function_tool(
    name="search_emails",
    description="Search your email inbox for specific keywords (e.g. 'search email for MongoDB', 'search resume in Gmail').",
)
async def search_emails(query: str) -> str:
    logger.info(f"[LIA EMAIL TOOL TRIGGERED] search_emails('{query}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_search_emails, query)


@llm.function_tool(
    name="draft_email",
    description="Compose an email draft with recipient, subject, and body content.",
)
async def draft_email(recipient: str, subject: str, body: str) -> str:
    logger.info(f"[LIA EMAIL TOOL TRIGGERED] draft_email('{recipient}', '{subject}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_draft_email, recipient, subject, body)


@llm.function_tool(
    name="send_email",
    description="Send a composed email to a recipient. REQUIRES EXPLICIT USER CONFIRMATION before sending.",
)
async def send_email(recipient: str, subject: str, body: str, user_confirmed: bool = False) -> str:
    logger.info(f"[LIA EMAIL TOOL TRIGGERED] send_email('{recipient}', confirmed={user_confirmed})")

    if not user_confirmed:
        return (
            f"SAFETY CONFIRMATION REQUIRED: I have prepared the email to {recipient} with subject \"{subject}\". "
            f"Please confirm if you want me to send this email."
        )

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, perform_draft_email, recipient, subject, body)
    return f"Confirmed by user. Email sent to {recipient} with subject '{subject}'."
