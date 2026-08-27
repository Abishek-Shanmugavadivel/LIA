"""
Voice Configuration Manager for LIA JARVIS Experience (Phase 9)
Supports Configurable Voices:
- Female (Default): Warm natural female voice (Aoede), clear English, Tamil pronunciation support, Tanglish support.
- Female Calm: Calm, clear female voice (Kore).
- Male: Crisp natural male voice (Puck).
- Male Deep: Deep male AI voice (Fenrir).
- Custom: User defined voice identifier/settings.
"""

import os
import json
import logging
from memory.database import get_db_connection

logger = logging.getLogger("lia-voice-config")

# Available Gemini Realtime Voice Enums & Web TTS Mappings
AVAILABLE_VOICES = {
    "female": {
        "id": "Aoede",  # Warm, expressive female Gemini voice (Most natural female voice)
        "gender": "Female",
        "name": "Warm Female Voice (Default)",
        "description": "Warm, natural female AI voice with clear English, Tamil & Tanglish pronunciation",
        "language_support": ["English", "Tamil", "Tanglish"],
        "tts_code": "ta-IN-PallaviNeural",
        "provider": "google-realtime"
    },
    "female_warm": {
        "id": "Aoede",
        "gender": "Female",
        "name": "Warm Female Voice",
        "description": "Natural expressive female voice profile",
        "language_support": ["English", "Tamil", "Tanglish"],
        "tts_code": "en-US-Journey-F",
        "provider": "google-realtime"
    },
    "female_calm": {
        "id": "Kore",
        "gender": "Female",
        "name": "Calm Female Voice",
        "description": "Serene and clear female voice profile",
        "language_support": ["English", "Tamil", "Tanglish"],
        "tts_code": "en-US-AvaNeural",
        "provider": "google-realtime"
    },
    "male": {
        "id": "Puck",
        "gender": "Male",
        "name": "Natural Male Voice",
        "description": "Natural, crisp male AI voice",
        "language_support": ["English", "Tamil", "Tanglish"],
        "tts_code": "ta-IN-ValluvarNeural",
        "provider": "google-realtime"
    },
    "male_deep": {
        "id": "Fenrir",
        "gender": "Male",
        "name": "Deep Male Voice",
        "description": "Deep and resonant male voice profile",
        "language_support": ["English", "Tamil", "Tanglish"],
        "tts_code": "en-US-GuyNeural",
        "provider": "google-realtime"
    },
    "custom": {
        "id": "Kore",
        "gender": "Female",
        "name": "Custom Synthetic Voice Profile",
        "description": "Customized pitch, rate, and synthetic voice profile",
        "language_support": ["English", "Tamil", "Tanglish"],
        "tts_code": "en-US-AvaNeural",
        "provider": "custom"
    }
}


class VoiceManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VoiceManager, cls).__new__(cls)
            cls._instance._init_voice_table()
        return cls._instance

    def _init_voice_table(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS voice_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        # Ensure default voice is female if not present
        cursor.execute("SELECT value FROM voice_settings WHERE key = 'voice_type'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO voice_settings (key, value) VALUES ('voice_type', 'female')")

        # Default rate and pitch
        cursor.execute("SELECT value FROM voice_settings WHERE key = 'speaking_rate'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO voice_settings (key, value) VALUES ('speaking_rate', '1.0')")

        cursor.execute("SELECT value FROM voice_settings WHERE key = 'pitch'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO voice_settings (key, value) VALUES ('pitch', '0.0')")

        conn.commit()
        conn.close()

    def get_current_voice(self) -> dict:
        """Returns the active voice configuration dictionary."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM voice_settings")
        rows = dict(cursor.fetchall())
        conn.close()
        
        voice_type = rows.get("voice_type", "female")
        speaking_rate = rows.get("speaking_rate", "1.0")
        pitch = rows.get("pitch", "0.0")

        voice_info = AVAILABLE_VOICES.get(voice_type, AVAILABLE_VOICES["female"])
        return {
            "type": voice_type,
            "gender": voice_info.get("gender", "Female"),
            "voice_id": voice_info["id"],
            "name": voice_info["name"],
            "description": voice_info["description"],
            "language_support": voice_info["language_support"],
            "tts_code": voice_info["tts_code"],
            "provider": voice_info.get("provider", "google-realtime"),
            "speaking_rate": speaking_rate,
            "pitch": pitch,
            "is_default": (voice_type == "female")
        }

    def set_voice_type(self, voice_type: str) -> dict:
        """Sets active voice type (female, female_warm, female_calm, male, male_deep, custom)."""
        v_clean = voice_type.strip().lower() if voice_type else "female"
        if v_clean not in AVAILABLE_VOICES:
            v_clean = "female"

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO voice_settings (key, value) VALUES ('voice_type', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (v_clean,))
        conn.commit()
        conn.close()
        
        logger.info(f"Voice setting updated to: {v_clean}")
        return self.get_current_voice()

    def update_voice_settings(self, voice_type: str = None, speaking_rate: str = None, pitch: str = None) -> dict:
        """Updates voice type, speaking rate, and/or pitch settings."""
        conn = get_db_connection()
        cursor = conn.cursor()

        if voice_type:
            v_clean = voice_type.strip().lower()
            if v_clean in AVAILABLE_VOICES:
                cursor.execute("""
                    INSERT INTO voice_settings (key, value) VALUES ('voice_type', ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """, (v_clean,))

        if speaking_rate is not None:
            cursor.execute("""
                INSERT INTO voice_settings (key, value) VALUES ('speaking_rate', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (str(speaking_rate),))

        if pitch is not None:
            cursor.execute("""
                INSERT INTO voice_settings (key, value) VALUES ('pitch', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (str(pitch),))

        conn.commit()
        conn.close()
        return self.get_current_voice()

    def get_all_voices(self) -> dict:
        """Returns all available voice profiles."""
        return AVAILABLE_VOICES


_voice_manager_instance = None


def get_voice_manager() -> VoiceManager:
    global _voice_manager_instance
    if _voice_manager_instance is None:
        _voice_manager_instance = VoiceManager()
    return _voice_manager_instance

