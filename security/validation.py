"""
Tool Parameter & Output Validation for LIA (Phase 8)
Sanitizes outputs, masks secrets (API keys, LiveKit secrets), and validates tool parameters.
"""

import os
import re
from typing import Tuple, Dict, Any, Union
from security.permissions import check_permission, PermissionLevel

# Common secret regex patterns (API keys, tokens, JWTs, secrets)
SECRET_PATTERNS = [
    r"LIVEKIT_API_SECRET=['\"]?([A-Za-z0-9_\-]{16,})['\"]?",
    r"LIVEKIT_API_KEY=['\"]?([A-Za-z0-9_\-]{10,})['\"]?",
    r"GOOGLE_API_KEY=['\"]?([A-Za-z0-9_\-]{20,})['\"]?",
    r"AIzaSy[A-Za-z0-9_\-]{33}", # Google API Key pattern
    r"sk-[A-Za-z0-9]{32,}",       # OpenAI pattern if present
    r"bearer\s+[A-Za-z0-9\-\._~\+\/]+=*",
]

def mask_secrets(text: str) -> str:
    """
    Redacts sensitive credentials, API keys, and LiveKit secrets from any output text or logs.
    """
    if not isinstance(text, str):
        text = str(text)
        
    masked = text
    # Also mask active environment variable values if present in text
    for env_var in ["LIVEKIT_API_SECRET", "LIVEKIT_API_KEY", "GOOGLE_API_KEY", "TAVILY_API_KEY"]:
        val = os.getenv(env_var)
        if val and len(val) > 4:
            masked = masked.replace(val, f"[REDACTED_{env_var}]")
            
    for pattern in SECRET_PATTERNS:
        masked = re.sub(pattern, "[REDACTED_SECRET]", masked, flags=re.IGNORECASE)
        
    return masked

def sanitize_output(output_data: Union[str, dict, list]) -> Union[str, dict, list]:
    """Recursively masks secrets in string or dict structures."""
    if isinstance(output_data, str):
        return mask_secrets(output_data)
    elif isinstance(output_data, dict):
        return {k: sanitize_output(v) for k, v in output_data.items()}
    elif isinstance(output_data, list):
        return [sanitize_output(item) for item in output_data]
    return output_data

def validate_tool_call(tool_name: str, args: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validates a tool invocation prior to execution.
    Returns (is_allowed: bool, message: str, sanitized_args: Dict).
    """
    perm_level, reason = check_permission(tool_name, args)
    
    if perm_level == PermissionLevel.BLOCKED:
        return False, f"Security Violation: {reason}", args
    elif perm_level == PermissionLevel.HIGH_RISK:
        return False, f"High-Risk Action Notice: {reason}", args
        
    # Sanitize input args
    sanitized_args = sanitize_output(args)
    if not isinstance(sanitized_args, dict):
        sanitized_args = args
        
    return True, "Tool call validated successfully.", sanitized_args
