"""
Desktop Device Abstraction for LIA (Phase 7 + Phase 8)
Represents the local or remote Windows/desktop workstation and its tool capabilities.
"""

import platform
import psutil
from devices.registry import get_device_registry
from tools.system import perform_get_system_info

class DesktopDevice:
    def __init__(self, device_id: str = "desktop_primary", name: str = "Primary Computer"):
        self.device_id = device_id
        self.name = name
        self.registry = get_device_registry()
        self.sync_telemetry()

    def sync_telemetry(self):
        """Fetch system information and update central registry."""
        battery_level = 100
        try:
            battery = psutil.sensors_battery()
            if battery:
                battery_level = int(battery.percent)
        except Exception:
            battery_level = 100

        sys_str = perform_get_system_info("all")

        self.registry.register_device(
            device_id=self.device_id,
            name=self.name,
            device_type="desktop",
            platform=platform.system(),
            status="connected",
            battery=battery_level,
            network="Ethernet/Wi-Fi",
            extra_info={"telemetry": sys_str}
        )

    def get_status(self):
        """Returns the registered status for this desktop device."""
        self.sync_telemetry()
        return self.registry.get_device(self.device_id)
