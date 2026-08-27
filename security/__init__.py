"""
Security Package for LIA Assistant (Phase 8)
Provides safety checks, permission validation, credential masking, and high-risk command enforcement.
"""

from security.permissions import (
    PermissionLevel,
    check_permission,
    is_high_risk_action,
    HIGH_RISK_COMMANDS,
)
from security.validation import (
    validate_tool_call,
    sanitize_output,
    mask_secrets,
)

__all__ = [
    "PermissionLevel",
    "check_permission",
    "is_high_risk_action",
    "HIGH_RISK_COMMANDS",
    "validate_tool_call",
    "sanitize_output",
    "mask_secrets",
]
