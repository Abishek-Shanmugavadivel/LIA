"""
System Information Tools for LIA (Phase 4)
Retrieves safe system telemetry such as CPU usage, RAM usage, Battery level, Disk space, and OS information using psutil and platform.
"""

import os
import platform
import logging
import asyncio
import psutil
from livekit.agents import llm

logger = logging.getLogger("lia-tools-system")


def perform_get_system_info(metric: str = "all") -> str:
    """Synchronous helper to retrieve system metrics."""
    cleaned = metric.strip().lower() if metric else "all"

    logger.info(f"Retrieving system info metrics for category: '{cleaned}'")
    info_parts = []

    # OS Info
    if cleaned in ["all", "os", "system", "operating system"]:
        sys_os = platform.system()
        sys_release = platform.release()
        sys_arch = platform.architecture()[0]
        info_parts.append(f"Operating System: {sys_os} {sys_release} ({sys_arch})")

    # CPU Info
    if cleaned in ["all", "cpu", "processor"]:
        cpu_usage = psutil.cpu_percent(interval=0.3)
        cpu_count = psutil.cpu_count(logical=True)
        info_parts.append(f"CPU Usage: {cpu_usage}% across {cpu_count} logical cores")

    # RAM Info
    if cleaned in ["all", "ram", "memory"]:
        ram = psutil.virtual_memory()
        total_gb = round(ram.total / (1024**3), 2)
        used_gb = round(ram.used / (1024**3), 2)
        available_gb = round(ram.available / (1024**3), 2)
        info_parts.append(
            f"RAM Memory: {ram.percent}% used ({used_gb} GB used out of {total_gb} GB total, {available_gb} GB free)"
        )

    # Disk Info
    if cleaned in ["all", "disk", "storage", "drive", "space"]:
        try:
            drive_letter = "C:\\" if platform.system() == "Windows" else "/"
            disk = psutil.disk_usage(drive_letter)
            disk_total_gb = round(disk.total / (1024**3), 2)
            disk_free_gb = round(disk.free / (1024**3), 2)
            info_parts.append(
                f"Disk Storage ({drive_letter}): {disk.percent}% used ({disk_free_gb} GB free out of {disk_total_gb} GB total)"
            )
        except Exception as e:
            logger.warning(f"Could not retrieve disk usage: {e}")

    # Battery Info
    if cleaned in ["all", "battery", "power"]:
        try:
            battery = psutil.sensors_battery()
            if battery:
                plugged = "Plugged in (Charging)" if battery.power_plugged else "Discharging (On Battery)"
                info_parts.append(f"Battery Status: {battery.percent}% ({plugged})")
            else:
                info_parts.append("Battery Status: Desktop / No battery detected")
        except Exception as e:
            logger.warning(f"Battery info error: {e}")

    if not info_parts:
        return "Could not determine system metric. Available metrics: CPU, RAM, Disk, Battery, OS."

    return "\n".join(info_parts)


@llm.function_tool(
    name="get_system_information",
    description=(
        "Retrieve system telemetry and status on the user's computer including CPU usage percentage, "
        "RAM memory usage, disk storage space, battery level, and operating system info. "
        "Parameter metric can be 'cpu', 'ram', 'disk', 'battery', 'os', or 'all'."
    ),
)
async def get_system_information(metric: str = "all") -> str:
    """LiveKit tool wrapper for system information."""
    logger.info(f"[LIA SYSTEM TOOL TRIGGERED] get_system_information(metric='{metric}')")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_get_system_info, metric)
