"""
Permissions and High-Risk Action Safety Engine for LIA (Phase 8)
Defines safety policies, permission levels, and high-risk action guards.
"""

from enum import Enum
import re
from typing import Tuple, Dict, Any

class PermissionLevel(Enum):
    SAFE = "safe"
    NORMAL = "normal"
    HIGH_RISK = "high_risk"
    BLOCKED = "blocked"

# List of high-risk actions that require explicit safety confirmation or are strictly blocked
HIGH_RISK_COMMANDS = {
    "format_disk": "Formatting disks or partitions is strictly blocked.",
    "shutdown_system": "System shutdown requires explicit manual user confirmation.",
    "restart_system": "System restart requires explicit manual user confirmation.",
    "delete_system_files": "Deleting system root files or OS components is strictly blocked.",
    "install_unknown_software": "Installing unverified third-party software requires user confirmation.",
    "change_passwords": "Password or credential alteration is strictly blocked.",
    "financial_transactions": "Financial transactions or purchases are strictly blocked.",
    "send_email": "Sending emails requires explicit user confirmation.",
    "send_messages": "Sending external messaging payloads requires explicit confirmation.",
}

# Dangerous shell patterns to prevent arbitrary command injection
DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"format\s+[c-z]:",
    r"del\s+/s\s+/q\s+c:\\windows",
    r"shutdown\s+/s",
    r"drop\s+database",
    r"mkfs",
    r"dd\s+if=",
]

def is_high_risk_action(action_name: str) -> bool:
    """Checks if an action name matches known high-risk commands."""
    action_lower = action_name.lower().strip()
    return action_lower in HIGH_RISK_COMMANDS or any(k in action_lower for k in HIGH_RISK_COMMANDS)

def check_permission(tool_name: str, args: Dict[str, Any]) -> Tuple[PermissionLevel, str]:
    """
    Evaluates a tool call and parameters for safety compliance.
    Returns (PermissionLevel, reason_string).
    """
    tool_lower = tool_name.lower().strip()
    
    # Check for direct high-risk command matches
    if is_high_risk_action(tool_lower):
        reason = HIGH_RISK_COMMANDS.get(tool_lower, "High-risk system modification blocked.")
        return PermissionLevel.HIGH_RISK, reason
        
    # Check for dangerous patterns in arguments
    args_str = str(args).lower()
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, args_str, re.IGNORECASE):
            return PermissionLevel.BLOCKED, f"Blocked: Potentially dangerous command pattern detected ('{pattern}')."
            
    # Check specific tool parameter safety
    if tool_lower in ("open_application", "close_application"):
        app_name = str(args.get("app_name", "")).lower()
        if any(bad in app_name for bad in ["cmd.exe /c format", "powershell -enc", "vssadmin delete"]):
            return PermissionLevel.BLOCKED, "Blocked malicious application execution payload."

    if tool_lower in ("open_url", "navigate_url", "browser_open_url"):
        url = str(args.get("url", "")).strip().lower()
        if not is_safe_url(url):
            return PermissionLevel.BLOCKED, f"Blocked: Dangerous or invalid URL scheme/target ('{url}'). Only http and https schemes are permitted."

    if tool_lower in ("type_text", "browser_type"):
        selector = str(args.get("selector", "")).lower()
        field_type = str(args.get("field_type", "")).lower()
        content = str(args.get("text", "")).lower()
        sensitive_kw = ["password", "passwd", "credit_card", "cvv", "social_security", "ssn", "secret_key", "auth_token"]
        if any(kw in selector or kw in field_type for kw in sensitive_kw):
            return PermissionLevel.BLOCKED, "Blocked: Typing into sensitive password or credential fields is strictly prohibited."

    if tool_lower == "remember_information":
        category = str(args.get("category", "")).lower()
        content = str(args.get("content", "")).lower()
        # Prevent storing credentials or sensitive tokens in persistent memory
        sensitive_keywords = ["api_key", "password", "secret", "private_key", "bearer_token", "credit_card", "cvv"]
        if any(kw in category or kw in content for kw in sensitive_keywords):
            return PermissionLevel.BLOCKED, "Blocked: Storing API keys, passwords, or credentials in persistent memory is strictly prohibited."

    return PermissionLevel.SAFE, "Action approved."


def is_safe_url(url_str: str) -> bool:
    """
    Validates that a URL uses http or https schemes only, rejecting dangerous schemes like
    javascript:, data:, file:, about:, chrome:, edge:, and malformed targets.
    """
    if not url_str:
        return False
    u = url_str.strip().lower()
    
    # Reject explicitly forbidden dangerous schemes
    forbidden_schemes = ["javascript:", "data:", "file:", "about:", "chrome:", "edge:", "vbscript:"]
    if any(u.startswith(scheme) for scheme in forbidden_schemes):
        return False

    # Check url parse scheme if scheme is provided
    try:
        from urllib.parse import urlparse
        parsed = urlparse(u if "://" in u else f"https://{u}")
        if parsed.scheme and parsed.scheme not in ("http", "https"):
            return False
        if not parsed.netloc and not parsed.path:
            return False
    except Exception:
        return False

    return True

