"""
Standardized Tool Result Format & Action Verification Helper for LIA Tools.
Ensures every tool call returns structured telemetry:
{
  "success": bool,
  "tool": str,
  "action": str,
  "result": str / dict,
  "error": Optional[str],
  "duration": float
}
Also provides empirical post-execution verification helpers.
"""

import os
import time
import psutil
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("lia-tool-result")


def create_tool_result(
    tool: str,
    action: str,
    success: bool,
    result: Any,
    error: Optional[str] = None,
    duration: float = 0.0
) -> Dict[str, Any]:
    """Formats a structured tool execution result."""
    return {
        "success": bool(success),
        "tool": tool,
        "action": action,
        "result": result,
        "error": error,
        "duration": round(duration, 3)
    }


def verify_process_running(process_names: list[str], max_wait_seconds: float = 2.0) -> bool:
    """Empirically verifies if a process matching process_names is active."""
    start = time.time()
    while time.time() - start <= max_wait_seconds:
        try:
            for proc in psutil.process_iter(["name"]):
                p_name = proc.info.get("name")
                if p_name and any(target.lower() in p_name.lower() for target in process_names):
                    return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


def verify_file_created(file_path: str, max_wait_seconds: float = 2.0) -> bool:
    """Empirically verifies if a file exists on disk."""
    start = time.time()
    while time.time() - start <= max_wait_seconds:
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return True
        time.sleep(0.3)
    return False
