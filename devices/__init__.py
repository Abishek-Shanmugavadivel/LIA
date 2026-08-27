"""
Device Management Package for LIA Assistant (Phase 7 + Phase 8)
Provides unified device registration, state tracking, and device-aware action routing.
"""

from devices.registry import DeviceRegistry, get_device_registry
from devices.desktop import DesktopDevice
from devices.mobile import MobileDevice

__all__ = [
    "DeviceRegistry",
    "get_device_registry",
    "DesktopDevice",
    "MobileDevice",
]
