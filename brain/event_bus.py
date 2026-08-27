"""
Central Event Bus for LIA Architecture (Phase 17)
Provides a decoupled publish-subscribe event system for core components, plugins,
and device background listeners without direct tight coupling.
"""

import logging
from typing import Dict, Any, List, Callable, Optional

logger = logging.getLogger("lia-event-bus")


class EventType:
    TASK_STARTED = "TASK_STARTED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"
    REMINDER_CREATED = "REMINDER_CREATED"
    REMINDER_TRIGGERED = "REMINDER_TRIGGERED"
    CALENDAR_UPDATED = "CALENDAR_UPDATED"
    PLUGIN_ENABLED = "PLUGIN_ENABLED"
    PLUGIN_DISABLED = "PLUGIN_DISABLED"
    PLUGIN_FAILED = "PLUGIN_FAILED"
    DEVICE_CONNECTED = "DEVICE_CONNECTED"
    DEVICE_DISCONNECTED = "DEVICE_DISCONNECTED"
    VOICE_STARTED = "VOICE_STARTED"
    VOICE_COMPLETED = "VOICE_COMPLETED"
    VISION_UPDATED = "VISION_UPDATED"
    PROJECT_CHANGED = "PROJECT_CHANGED"


class CentralEventBus:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(CentralEventBus, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}

    def subscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Registers a subscriber callback handler for a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)
            logger.info(f"Subscribed handler {handler.__name__ if hasattr(handler, '__name__') else handler} to {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Unsubscribes a callback handler."""
        if event_type in self._subscribers and handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Dispatches an event payload to all registered subscribers safely."""
        subscribers = self._subscribers.get(event_type, [])
        logger.info(f"Publishing event '{event_type}' to {len(subscribers)} subscribers.")
        for handler in subscribers:
            try:
                handler(payload)
            except Exception as err:
                logger.error(f"Error in event handler for {event_type}: {err}")


_global_event_bus: Optional['CentralEventBus'] = None


def get_event_bus() -> CentralEventBus:
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = CentralEventBus()
    return _global_event_bus
