"""
LIA System Tray Controller
Provides Windows System Tray integration with visual state indicators (Online, Listening, Busy, Offline, Error)
and tray menu actions (Start, Stop, Restart, Open, Exit).
"""

import os
import sys
import logging
import threading
import webbrowser
from PIL import Image, ImageDraw

if sys.platform == "win32":
    try:
        import pystray
        from pystray import MenuItem as item, Menu
    except Exception:
        pystray = None
else:
    pystray = None

from process_manager import get_process_manager
from voice.state_machine import get_state_machine, LIAState

logger = logging.getLogger("lia-system-tray")


def create_status_icon(color: str = "cyan") -> Image.Image:
    """Generates a dynamic status icon image for the system tray."""
    width = 64
    height = 64
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Base circle (outer glow)
    color_map = {
        "cyan": (0, 229, 255),       # Online
        "green": (0, 230, 118),      # Listening
        "orange": (255, 145, 0),     # Busy
        "red": (255, 23, 68),        # Error / Offline
        "gray": (158, 158, 158)      # Stopped
    }
    rgb = color_map.get(color, (0, 229, 255))
    
    draw.ellipse((4, 4, 60, 60), fill=(rgb[0], rgb[1], rgb[2], 230), outline=(255, 255, 255, 255), width=2)
    # LIA inner emblem text
    draw.text((18, 22), "LIA", fill=(255, 255, 255))
    return image


class LIASystemTray:
    def __init__(self):
        self.pm = get_process_manager()
        self.sm = get_state_machine()
        self.icon: pystray.Icon = None
        self._running = False

    def _get_current_color(self) -> str:
        status_info = self.pm.status()
        if not status_info.get("running"):
            return "gray"
        state = self.sm.get_state()
        if state == LIAState.LISTENING:
            return "green"
        elif state in [LIAState.THINKING, LIAState.EXECUTING, LIAState.SPEAKING]:
            return "orange"
        elif state == LIAState.ERROR:
            return "red"
        return "cyan"

    def _on_start(self, icon, item):
        res = self.pm.start()
        logger.info(f"Tray command Start: {res}")
        self.update_tray()

    def _on_stop(self, icon, item):
        res = self.pm.stop()
        logger.info(f"Tray command Stop: {res}")
        self.update_tray()

    def _on_restart(self, icon, item):
        res = self.pm.restart()
        logger.info(f"Tray command Restart: {res}")
        self.update_tray()

    def _on_open_mobile(self, icon, item):
        webbrowser.open("http://localhost:8080/")

    def _on_exit(self, icon, item):
        logger.info("Exiting System Tray...")
        self._running = False
        if self.icon:
            self.icon.stop()

    def update_tray(self):
        if self.icon:
            color = self._get_current_color()
            self.icon.icon = create_status_icon(color)
            state_str = self.sm.get_state()
            self.icon.title = f"LIA Assistant — {state_str}"

    def run(self, daemon: bool = False):
        if not pystray or sys.platform != "win32":
            logger.info("System tray integration is disabled on non-Windows/headless OS.")
            return

        menu = Menu(
            item("LIA Online / Status", lambda icon, item: None, enabled=False),
            item("Start LIA", self._on_start),
            item("Stop LIA", self._on_stop),
            item("Restart LIA", self._on_restart),
            item("Open LIA Web", self._on_open_mobile),
            item("Exit Tray", self._on_exit)
        )

        initial_color = self._get_current_color()
        self.icon = pystray.Icon("LIA", create_status_icon(initial_color), "LIA Personal AI Assistant", menu)
        self._running = True

        if daemon:
            t = threading.Thread(target=self.icon.run, daemon=True)
            t.start()
        else:
            self.icon.run()


def get_system_tray() -> LIASystemTray:
    return LIASystemTray()
