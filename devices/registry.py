"""
Unified Device Registry for LIA (Phase 7 + Phase 8)
Tracks active connected devices (desktop, mobile, tablet), their telemetry, online status, and capabilities.
"""

import time
import platform
import threading
from typing import Dict, Any, List, Optional

class DeviceRegistry:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DeviceRegistry, cls).__new__(cls)
                cls._instance._devices = {}
                cls._instance._init_default_devices()
            return cls._instance

    def _init_default_devices(self):
        """Initializes default known device slots for Desktop and Mobile."""
        # Auto-register local host desktop
        sys_plat = platform.system()
        self.register_device(
            device_id="desktop_primary",
            name="Primary Computer",
            device_type="desktop",
            platform=sys_plat,
            status="connected",
            battery=100,
            network="Ethernet/Wi-Fi",
            extra_info={"screen_count": 1, "os": sys_plat}
        )

    def register_device(
        self,
        device_id: str,
        name: str,
        device_type: str,
        platform: str,
        status: str = "connected",
        battery: Optional[int] = None,
        network: Optional[str] = "online",
        extra_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Registers or updates a device record in the central registry."""
        with self._lock:
            device_entry = {
                "id": device_id,
                "name": name,
                "type": device_type.lower(),
                "platform": platform,
                "status": status,
                "battery": battery if battery is not None else 100,
                "network": network or "online",
                "last_seen": time.time(),
                "extra_info": extra_info or {},
            }
            self._devices[device_id] = device_entry
            return device_entry

    def update_status(
        self,
        device_id: str,
        status: str = "connected",
        battery: Optional[int] = None,
        network: Optional[str] = None,
        extra_info: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Updates runtime telemetry (battery, status, network) for a specific device."""
        with self._lock:
            if device_id in self._devices:
                dev = self._devices[device_id]
                dev["status"] = status
                if battery is not None:
                    dev["battery"] = battery
                if network is not None:
                    dev["network"] = network
                dev["last_seen"] = time.time()
                if extra_info:
                    dev["extra_info"].update(extra_info)
                return dev
            return None

    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single device by ID."""
        with self._lock:
            return self._devices.get(device_id)

    def get_device_by_type(self, device_type: str) -> List[Dict[str, Any]]:
        """Retrieves list of devices matching a specific device type ('desktop' or 'mobile')."""
        target_type = device_type.lower().strip()
        with self._lock:
            return [
                dev for dev in self._devices.values()
                if dev["type"] == target_type
            ]

    def list_devices(self) -> List[Dict[str, Any]]:
        """Returns all registered devices in the system."""
        with self._lock:
            # Check timeout for idle/disconnected (e.g. 5 minutes no heartbeat for mobile)
            now = time.time()
            for dev in self._devices.values():
                if dev["type"] == "mobile" and (now - dev["last_seen"]) > 300:
                    dev["status"] = "disconnected"
            return list(self._devices.values())

    def list_registered_devices(self) -> List[Dict[str, Any]]:
        """Alias for list_devices."""
        return self.list_devices()

    def normalize_device_target(self, target_str: str) -> str:
        """
        Translates natural user language device targets into registered device categories ('desktop' or 'mobile').
        Examples:
          "laptop", "computer", "my PC", "windows" -> "desktop"
          "phone", "mobile", "android", "iphone" -> "mobile"
        """
        target_lower = target_str.lower().strip()
        desktop_keywords = ["computer", "laptop", "desktop", "pc", "windows", "mac"]
        mobile_keywords = ["phone", "mobile", "android", "iphone", "mobile app", "smartphone"]

        if any(kw in target_lower for kw in desktop_keywords):
            return "desktop"
        if any(kw in target_lower for kw in mobile_keywords):
            return "mobile"
            
        return "desktop" # Default fallback

def get_device_registry() -> DeviceRegistry:
    return DeviceRegistry()
