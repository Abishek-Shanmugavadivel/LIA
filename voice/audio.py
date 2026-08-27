"""
Audio Utilities & Noise Cancellation Helper for LIA Voice Stream (Phase 8)
Provides audio frame processing, noise cancellation configuration, and energy threshold VAD helper.
"""

import logging
from typing import Optional

logger = logging.getLogger("lia-audio")

def check_audio_energy(audio_bytes: bytes, threshold: int = 500) -> bool:
    """Simple RMS energy helper to detect voice activity in raw PCM audio frames."""
    if not audio_bytes or len(audio_bytes) < 2:
        return False
    # Calculate simple peak amplitude
    try:
        import struct
        samples = struct.unpack(f"{len(audio_bytes)//2}h", audio_bytes)
        max_amp = max(abs(s) for s in samples)
        return max_amp > threshold
    except Exception:
        return True
