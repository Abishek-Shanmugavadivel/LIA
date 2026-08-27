"""
Voice Settings Tools for LIA Agent (Phase 9 JARVIS Experience)
Provides function tools to query active voice configuration and dynamically modify voice profiles,
rate, and pitch (defaulting to the natural female voice 'Aoede').
"""

import logging
from typing import Annotated
from livekit.agents import llm
from voice.voice_config import get_voice_manager, AVAILABLE_VOICES

logger = logging.getLogger("lia-tools-voice")


def perform_get_voice_settings() -> str:
    """Synchronous helper to retrieve formatted active voice settings."""
    voice_mgr = get_voice_manager()
    curr = voice_mgr.get_current_voice()
    
    return (
        f"LIA Voice Settings:\n"
        f"- Active Voice Type: {curr['type']} ({curr['name']})\n"
        f"- Voice ID: {curr['voice_id']}\n"
        f"- Gender: {curr['gender']}\n"
        f"- Provider: {curr['provider']}\n"
        f"- TTS Code: {curr['tts_code']}\n"
        f"- Speaking Rate: {curr['speaking_rate']}\n"
        f"- Pitch: {curr['pitch']}\n"
        f"- Default Voice: {'Yes (Natural Female)' if curr['is_default'] else 'No'}\n"
        f"- Description: {curr['description']}"
    )


def perform_change_voice_setting(
    voice_type: str = "female",
    speaking_rate: str = None,
    pitch: str = None
) -> str:
    """Synchronous helper to update voice configuration."""
    voice_mgr = get_voice_manager()
    v_clean = voice_type.strip().lower() if voice_type else "female"
    
    # Normalize common user voice names to supported keys
    if v_clean in ["female", "woman", "lady", "girl", "default", "aoede"]:
        v_clean = "female"
    elif v_clean in ["female_warm", "warm"]:
        v_clean = "female_warm"
    elif v_clean in ["female_calm", "calm"]:
        v_clean = "female_calm"
    elif v_clean in ["male", "man", "boy", "puck"]:
        v_clean = "male"
    elif v_clean in ["male_deep", "deep"]:
        v_clean = "male_deep"

    updated = voice_mgr.update_voice_settings(
        voice_type=v_clean,
        speaking_rate=speaking_rate,
        pitch=pitch
    )

    return (
        f"Voice setting updated successfully!\n"
        f"- Active Voice: {updated['name']} (ID: {updated['voice_id']})\n"
        f"- Gender: {updated['gender']}\n"
        f"- Rate: {updated['speaking_rate']} | Pitch: {updated['pitch']}\n"
        f"- Status: {'Set to Natural Female Default' if updated['is_default'] else 'Custom Voice Active'}"
    )


@llm.function_tool(
    name="get_voice_settings",
    description="Retrieves active LIA voice configuration settings, including voice type, gender, voice ID, speaking rate, and pitch."
)
async def get_voice_settings() -> str:
    """Tool to check current voice settings."""
    logger.info("Executing tool: get_voice_settings")
    return perform_get_voice_settings()


@llm.function_tool(
    name="change_voice_setting",
    description="Changes LIA's voice settings. Supports voice_type ('female' [default warm female], 'female_warm', 'female_calm', 'male', 'male_deep', 'custom'), speaking_rate, and pitch."
)
async def change_voice_setting(
    voice_type: str = "female",
    speaking_rate: str = None,
    pitch: str = None
) -> str:
    """Tool to update voice settings."""
    logger.info(f"Executing tool: change_voice_setting with voice_type='{voice_type}', rate='{speaking_rate}', pitch='{pitch}'")
    return perform_change_voice_setting(voice_type, speaking_rate, pitch)

