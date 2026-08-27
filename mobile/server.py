"""
Mobile Backend Server for LIA (Phases 7–9 JARVIS Experience)
Provides secure HTTP endpoints for LiveKit Token Generation, Device Telemetry Sync,
News, Reminders, Calendar, Voice Settings, JARVIS Modes, Push Notifications, and Mobile Web Client serving.
NEVER exposes LIVEKIT_API_SECRET to the client application.
"""

import os
import sys
import time
import json
import logging
import threading

# Ensure root project directory is in sys.path for direct python execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
from http.server import HTTPServer, SimpleHTTPRequestHandler

load_dotenv(".env")
from urllib.parse import parse_qs, urlparse
from livekit.api import AccessToken, VideoGrants
from devices.registry import get_device_registry
from security.validation import mask_secrets
from tools.news import perform_get_news
from tools.reminders import perform_get_reminders, perform_create_reminder
from tools.calendar_tools import perform_get_calendar_events, perform_add_calendar_event
from voice.voice_config import get_voice_manager
from brain.modes import get_active_mode, perform_activate_jarvis_mode

logger = logging.getLogger("lia-mobile-server")

def generate_mobile_token(identity: str = "lia_mobile_user", room_name: str = "lia_default_room") -> str:
    """Generates a secure, short-lived signed LiveKit JWT AccessToken."""
    api_key = os.getenv("LIVEKIT_API_KEY", "")
    api_secret = os.getenv("LIVEKIT_API_SECRET", "")
    
    if not api_key or not api_secret:
        logger.error("Missing LIVEKIT_API_KEY or LIVEKIT_API_SECRET for token generation.")
        raise ValueError("LiveKit credentials not configured on server.")

    grant = VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True
    )

    token_obj = AccessToken(api_key, api_secret)
    token_obj.with_identity(identity)
    token_obj.with_name(identity)
    token_obj.with_grants(grant)
    
    return token_obj.to_jwt()

class MobileAPIRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Default directory for static mobile files
        app_dir = os.path.join(os.path.dirname(__file__), "app")
        super().__init__(*args, directory=app_dir, **kwargs)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/mobile/devices":
            registry = get_device_registry()
            devices = registry.list_devices()
            self._send_json({"status": "success", "devices": devices})
            return
        elif parsed.path == "/api/mobile/token":
            try:
                token = generate_mobile_token()
                livekit_url = os.getenv("LIVEKIT_URL", "wss://livekit.cloud")
                self._send_json({
                    "status": "success",
                    "token": token,
                    "url": livekit_url,
                    "room": "lia_default_room"
                })
            except Exception as e:
                self._send_json({"status": "error", "message": str(e)}, status_code=500)
            return
        elif parsed.path == "/api/mobile/news":
            news = perform_get_news(topic_or_category="technology", timeframe="latest")
            self._send_json({"status": "success", "news": news})
            return
        elif parsed.path == "/api/mobile/reminders":
            reminders = perform_get_reminders(filter_status="pending")
            self._send_json({"status": "success", "reminders": reminders})
            return
        elif parsed.path == "/api/mobile/calendar":
            calendar = perform_get_calendar_events(date_str="today")
            self._send_json({"status": "success", "calendar": calendar})
            return
        elif parsed.path == "/api/mobile/voice":
            voice_mgr = get_voice_manager()
            self._send_json({"status": "success", "voice": voice_mgr.get_current_voice()})
            return
        elif parsed.path == "/api/mobile/mode":
            self._send_json({"status": "success", "mode": get_active_mode()})
            return
        elif parsed.path == "/api/android/sync":
            from brain.task_agent import get_task_agent
            from health import get_health_monitor
            ta = get_task_agent()
            health = get_health_monitor().check_health()
            self._send_json({
                "status": "success",
                "android_sync": {
                    "task_state": ta.current_state,
                    "current_goal": ta.current_goal,
                    "health_status": health.get("status"),
                    "voice_profile": get_voice_manager().get_current_voice(),
                    "timestamp": time.time()
                }
            })
            return
        elif parsed.path in ["/health", "/status", "/api/health", "/api/status"]:
            registry = get_device_registry()
            voice_mgr = get_voice_manager()
            livekit_configured = bool(os.getenv("LIVEKIT_URL") and os.getenv("LIVEKIT_API_KEY") and os.getenv("LIVEKIT_API_SECRET"))
            gemini_configured = bool(os.getenv("GOOGLE_API_KEY"))
            
            # DB health check
            db_healthy = False
            try:
                from memory.database import get_db
                conn = get_db()
                conn.execute("SELECT 1")
                db_healthy = True
            except Exception:
                db_healthy = False

            health_info = {
                "status": "healthy" if (livekit_configured and gemini_configured and db_healthy) else "degraded",
                "backend": "online",
                "components": {
                    "livekit": {"configured": livekit_configured, "url": os.getenv("LIVEKIT_URL", "not_set")},
                    "gemini": {"configured": gemini_configured},
                    "database": {"connected": db_healthy},
                    "device_registry": {"total_devices": len(registry.list_devices())},
                    "mobile_server": {"running": True, "port": 8080},
                    "voice_system": voice_mgr.get_current_voice()
                }
            }
            self._send_json(health_info)
            return

        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length)
        
        try:
            data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception:
            data = {}

        if parsed.path == "/api/mobile/token":
            identity = data.get("identity", "lia_mobile_user")
            room_name = data.get("room", "lia_default_room")
            try:
                token = generate_mobile_token(identity=identity, room_name=room_name)
                livekit_url = os.getenv("LIVEKIT_URL", "wss://livekit.cloud")
                self._send_json({
                    "status": "success",
                    "token": token,
                    "url": livekit_url,
                    "room": room_name,
                    "identity": identity
                })
            except Exception as e:
                self._send_json({"status": "error", "message": str(e)}, status_code=500)
            return

        elif parsed.path in ["/api/orchestrate", "/api/mobile/command", "/api/android/command"]:
            command = data.get("command") or data.get("prompt") or data.get("text", "")
            if not command:
                self._send_json({"status": "error", "message": "Command parameter is required."}, status_code=400)
                return
            try:
                import asyncio
                from brain.orchestrator import LIAOrchestrator
                orchestrator = LIAOrchestrator()
                loop = asyncio.new_event_loop()
                res = loop.run_until_complete(orchestrator.process_request(command))
                loop.close()
                self._send_json({"status": "success", "result": res})
            except Exception as e:
                self._send_json({"status": "error", "message": str(e)}, status_code=500)
            return

        elif parsed.path in ["/api/mobile/status", "/api/android/telemetry"]:
            device_id = data.get("device_id", "android_primary")
            battery = data.get("battery", 85)
            network = data.get("network", "Wi-Fi")
            status = data.get("status", "connected")
            platform = data.get("platform", "Android Native")
            name = data.get("name", "User's Android Device")

            registry = get_device_registry()
            if not registry.get_device(device_id):
                registry.register_device(
                    device_id=device_id,
                    name=name,
                    device_type="mobile",
                    platform=platform,
                    status=status,
                    battery=battery,
                    network=network
                )
            else:
                registry.update_status(
                    device_id=device_id,
                    status=status,
                    battery=battery,
                    network=network,
                    extra_info={"platform": platform}
                )

            self._send_json({
                "status": "success",
                "device_id": device_id,
                "message": "Android telemetry updated successfully."
            })
            return

        elif parsed.path == "/api/android/notifications":
            title = data.get("title", "LIA Notification")
            message = data.get("message", "Task step update.")
            logger.info(f"[ANDROID NOTIFICATION PUSH] {title}: {message}")
            self._send_json({"status": "success", "pushed": True, "title": title, "message": message})
            return

        elif parsed.path == "/api/mobile/voice":
            v_type = data.get("voice_type", "female")
            rate = data.get("speaking_rate", None)
            pitch = data.get("pitch", None)
            voice_mgr = get_voice_manager()
            updated = voice_mgr.update_voice_settings(voice_type=v_type, speaking_rate=rate, pitch=pitch)
            self._send_json({"status": "success", "voice": updated})
            return

        elif parsed.path == "/api/mobile/mode":
            mode_name = data.get("mode", "coding")
            result = perform_activate_jarvis_mode(mode_name)
            self._send_json({"status": "success", "message": result, "mode": mode_name})
            return

        elif parsed.path == "/api/mobile/reminders":
            title = data.get("title", "Reminder")
            d_time = data.get("datetime_str", "6 PM")
            result = perform_create_reminder(title, d_time)
            self._send_json({"status": "success", "message": result})
            return

        elif parsed.path == "/api/mobile/calendar":
            title = data.get("title", "Meeting")
            d_str = data.get("date_str", "tomorrow")
            t_str = data.get("time_str", "3:00 PM")
            result = perform_add_calendar_event(title, d_str, t_str)
            self._send_json({"status": "success", "message": result})
            return

        self._send_json({"status": "error", "message": "Endpoint not found"}, status_code=404)

    def _send_json(self, data: dict, status_code: int = 200):
        try:
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
        except Exception as e:
            logger.debug(f"Socket write note: {e}")

    def log_message(self, format, *args):
        # Mask sensitive info in logs if any
        msg = format % args
        logger.debug(mask_secrets(msg))

def run_mobile_server(port: int = 8080, daemon: bool = True) -> HTTPServer:
    """Starts the HTTP server for mobile tokens and app serving."""
    server_address = ("", port)
    httpd = HTTPServer(server_address, MobileAPIRequestHandler)
    logger.info(f"LIA Mobile Backend Server running at http://localhost:{port}/")
    
    if daemon:
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
    return httpd

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server = run_mobile_server(port=8080, daemon=False)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Mobile server stopped.")
