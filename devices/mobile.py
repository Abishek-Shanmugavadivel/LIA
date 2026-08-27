"""
Mobile Device Abstraction for LIA (Phase 7 + Phase 8)
Represents a connected mobile client (Android/iOS) and handles mobile status reporting and push notifications.
"""

from devices.registry import get_device_registry

class MobileDevice:
    def __init__(self, device_id: str = "mobile_primary", name: str = "Primary Mobile Phone"):
        self.device_id = device_id
        self.name = name
        self.registry = get_device_registry()
        # Initialize default mobile status if not present
        if not self.registry.get_device(self.device_id):
            self.registry.register_device(
                device_id=self.device_id,
                name=self.name,
                device_type="mobile",
                platform="Android/iOS",
                status="connected",
                battery=85,
                network="Wi-Fi",
                extra_info={"app_version": "1.0.0", "livekit_connected": True}
            )

    def update_telemetry(self, battery: int, network: str, status: str = "connected", extra_info: dict = None):
        """Update mobile device telemetry from mobile HTTP API endpoint."""
        return self.registry.update_status(
            device_id=self.device_id,
            status=status,
            battery=battery,
            network=network,
            extra_info=extra_info
        )

    def get_status(self):
        """Retrieves mobile device status record."""
        return self.registry.get_device(self.device_id)
