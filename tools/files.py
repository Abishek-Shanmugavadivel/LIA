"""
File & Folder Control Tools for LIA (Phases 4-8 Expanded)
Handles finding files, opening files, creating safe folders, copying, moving, and renaming files.
Strictly blocks arbitrary or destructive system file deletion.
"""

import os
import sys
import shutil
import logging
import asyncio
from typing import Optional, List, Dict, Any
from livekit.agents import llm
from security.validation import validate_tool_call

logger = logging.getLogger("lia-tools-files")

# Safe root search directories
SAFE_SEARCH_DIRS = [
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/Desktop"),
    os.path.expanduser("~/Pictures"),
]


def perform_find_file(filename: str, search_dir: Optional[str] = None) -> Dict[str, Any]:
    """Synchronous helper to locate a file in safe user directories."""
    fn_clean = filename.strip().lower()
    target_dirs = [os.path.abspath(search_dir)] if search_dir and os.path.exists(search_dir) else SAFE_SEARCH_DIRS

    matches = []
    for s_dir in target_dirs:
        if not os.path.exists(s_dir):
            continue
        try:
            for root, dirs, files in os.walk(s_dir):
                for f in files:
                    if fn_clean in f.lower():
                        full_p = os.path.join(root, f)
                        matches.append({"name": f, "path": full_p, "size_bytes": os.path.getsize(full_p)})
                        if len(matches) >= 10:
                            break
                if len(matches) >= 10:
                    break
        except Exception as e:
            logger.warning(f"Error scanning directory {s_dir}: {e}")

    if matches:
        return {"status": "success", "count": len(matches), "matches": matches}
    return {"status": "not_found", "message": f"No file matching '{filename}' was found in safe user folders."}


def perform_open_file(filepath: str) -> str:
    """Synchronous helper to open a file with default OS application."""
    abs_path = os.path.abspath(filepath)
    if not os.path.exists(abs_path):
        return f"File path '{filepath}' does not exist."

    # Validate path is within user directory or safe temp
    user_home = os.path.expanduser("~")
    if not abs_path.startswith(user_home) and not abs_path.startswith(os.getenv("TEMP", "C:\\Windows\\Temp")):
        return f"Access Denied: Opening files outside user profile directory is restricted for security."

    try:
        if sys.platform == "win32":
            os.startfile(abs_path)
        else:
            subprocess.Popen(["xdg-open", abs_path])
        return f"Opened file '{os.path.basename(abs_path)}'."
    except Exception as e:
        logger.error(f"Error opening file '{abs_path}': {e}")
        return f"Could not open file: {e}"


def perform_create_folder(folder_name: str, parent_dir: Optional[str] = None) -> str:
    """Synchronous helper to create a folder in a safe directory."""
    fn_clean = folder_name.strip()
    base_dir = os.path.abspath(parent_dir) if parent_dir and os.path.exists(parent_dir) else os.path.expanduser("~/Documents")
    
    target_path = os.path.join(base_dir, fn_clean)
    try:
        os.makedirs(target_path, exist_ok=True)
        return f"Successfully created folder '{fn_clean}' at '{target_path}'."
    except Exception as e:
        logger.error(f"Error creating folder: {e}")
        return f"Could not create folder '{folder_name}': {e}"


def perform_copy_move_rename(action: str, src: str, dst: str) -> str:
    """Synchronous helper for safe file copy, move, or rename."""
    act = action.strip().lower()
    src_abs = os.path.abspath(src)
    dst_abs = os.path.abspath(dst)

    if not os.path.exists(src_abs):
        return f"Source path '{src}' does not exist."

    try:
        if act == "copy":
            if os.path.isdir(src_abs):
                shutil.copytree(src_abs, dst_abs, dirs_exist_ok=True)
            else:
                shutil.copy2(src_abs, dst_abs)
            return f"Copied '{os.path.basename(src_abs)}' to '{dst_abs}'."
        elif act in ["move", "rename"]:
            shutil.move(src_abs, dst_abs)
            return f"{act.title()}d '{os.path.basename(src_abs)}' to '{dst_abs}'."
        else:
            return f"Unknown file action '{action}'."
    except Exception as e:
        logger.error(f"Error performing {action}: {e}")
        return f"Could not perform {action}: {e}"


@llm.function_tool(
    name="find_file",
    description="Search your Documents, Downloads, Desktop, or Pictures folders for a file (e.g. 'find my resume', 'find report.pdf').",
)
async def find_file(filename: str, search_dir: Optional[str] = None) -> Dict[str, Any]:
    logger.info(f"[LIA FILES TOOL TRIGGERED] find_file('{filename}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_find_file, filename, search_dir)


@llm.function_tool(
    name="open_file",
    description="Open a file using its default desktop application.",
)
async def open_file(filepath: str) -> str:
    logger.info(f"[LIA FILES TOOL TRIGGERED] open_file('{filepath}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_open_file, filepath)


@llm.function_tool(
    name="create_folder",
    description="Create a new folder in Documents, Desktop, or Downloads (e.g. 'create a folder called LIA').",
)
async def create_folder(folder_name: str, parent_dir: Optional[str] = None) -> str:
    logger.info(f"[LIA FILES TOOL TRIGGERED] create_folder('{folder_name}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_create_folder, folder_name, parent_dir)


@llm.function_tool(
    name="manage_file",
    description="Copy, move, or rename a safe file or directory.",
)
async def manage_file(action: str, src_path: str, dst_path: str) -> str:
    logger.info(f"[LIA FILES TOOL TRIGGERED] manage_file(action='{action}', src='{src_path}', dst='{dst_path}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_copy_move_rename, action, src_path, dst_path)
