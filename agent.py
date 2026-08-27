import os
import sys
import logging
from dotenv import load_dotenv

# Reconfigure stdout for Windows console UTF-8 support
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv(".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("lia-agent")

logger.info("[BOOT] Starting LIA 5.0 JARVIS System Initialization...")
logger.info("[ENV] Validating Environment Variables...")

# Validate required environment variables before starting
REQUIRED_ENV_VARS = {
    "LIVEKIT_URL": "LiveKit WebSocket URL (e.g. wss://your-project.livekit.cloud)",
    "LIVEKIT_API_KEY": "LiveKit API Key",
    "LIVEKIT_API_SECRET": "LiveKit API Secret",
    "GOOGLE_API_KEY": "Google Gemini API Key for LLM and Realtime Audio",
}

missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    print("\n" + "=" * 60)
    print(" [LIA CRITICAL ERROR] Missing Required Environment Variables:")
    for var in missing_vars:
        print(f"  - {var}: {REQUIRED_ENV_VARS[var]}")
    print(" Please configure them in your .env file before starting LIA.")
    print("=" * 60 + "\n")
    logger.error(f"[ENV][ERROR] Missing environment variables: {missing_vars}")
else:
    logger.info("[ENV] All required environment variables validated successfully.")

from livekit import agents
from livekit.agents import AgentServer, AgentSession, Agent, room_io
from livekit.plugins import google, ai_coustics

from brain.prompts import LIA_SYSTEM_PROMPT, INITIAL_GREETING_PROMPT
from brain.conversation import ConversationManager
from brain.orchestrator import LIAOrchestrator
from tools import ALL_LIA_TOOLS
from devices import DesktopDevice, get_device_registry
from mobile.server import run_mobile_server
from voice.wakeword import WakeWordDetector, ConversationMode
from voice.state_machine import get_state_machine, LIAState
from voice.voice_config import get_voice_manager
from hotkey import get_hotkey_manager


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=LIA_SYSTEM_PROMPT, tools=ALL_LIA_TOOLS)


server = AgentServer()


@server.rtc_session(agent_name="lia-agent")
async def entrypoint(ctx: agents.JobContext):
    logger.info("[BOOT] Starting LiveKit RTC Job Context Entrypoint...")
    logger.info(f"[LIVEKIT] Room connected: {ctx.room.name}")
    
    # Initialize State Machine & Hotkey Manager
    state_machine = get_state_machine()
    state_machine.set_state(LIAState.STARTING)

    hotkey_mgr = get_hotkey_manager()
    hotkey_mgr.start(daemon=True)
    
    # Initialize Device Registry & Desktop Device Entry
    desktop_dev = DesktopDevice(device_id="desktop_primary", name="Primary Workstation")
    logger.info(f"[BOOT] Desktop Device registered: {desktop_dev.get_status()}")

    # Initialize Orchestrator & Wake Word engine
    orchestrator = LIAOrchestrator()
    wakeword_detector = WakeWordDetector(mode=ConversationMode.ACTIVE)
    conv_manager = ConversationManager(max_history_turns=10)

    # Voice Configuration Manager (Default: Warm Female Voice)
    voice_mgr = get_voice_manager()
    active_voice = voice_mgr.get_current_voice()
    logger.info(f"[TTS] Voice profile active: {active_voice['name']} (ID: {active_voice['voice_id']}, Gender: {active_voice['gender']})")

    # Command deduplication tracker
    last_cmd_text = ""
    last_cmd_time = 0.0

    try:
        logger.info("[GEMINI] Initializing Realtime Model (gemini-2.5-flash-native-audio-preview-12-2025)...")
        # Initialize Gemini Realtime Model with active voice configuration
        model = google.realtime.RealtimeModel(
            model="gemini-2.5-flash-native-audio-preview-12-2025",
            voice=active_voice["voice_id"],
            temperature=0.7,
            instructions=LIA_SYSTEM_PROMPT,
        )

        session = AgentSession(llm=model, tools=ALL_LIA_TOOLS)
        logger.info("[GEMINI] Gemini Realtime Model initialized successfully")
        logger.info("[LIVEKIT] Microphone & Audio Track active")
        logger.info("[LIVEKIT] Transcription event callback registered")

        # Track conversation turn events for context management & wake-word evaluation
        @session.on("user_input_transcribed")
        def on_user_transcribed(ev):
            nonlocal last_cmd_text, last_cmd_time
            if hasattr(ev, "transcript") and ev.transcript and ev.transcript.strip():
                import uuid
                import time as _time
                cmd_id = f"cmd-{uuid.uuid4().hex[:6]}"
                transcript = ev.transcript.strip()
                t_lower = transcript.lower()
                now = _time.time()

                logger.info(f"[AUDIO-IN][{cmd_id}] Audio track received from participant")
                logger.info(f"[TRANSCRIPT][{cmd_id}] {transcript}")

                # Deduplication check: ignore identical transcript within 2.5 seconds
                if t_lower == last_cmd_text and (now - last_cmd_time) < 2.5:
                    logger.info(f"[TRANSCRIPT][{cmd_id}] Duplicate transcript ignored: {transcript}")
                    return

                last_cmd_text = t_lower
                last_cmd_time = now

                current_st = state_machine.get_state()

                # Check if LIA is in SLEEPING state
                if current_st == LIAState.SLEEPING:
                    if any(w in t_lower for w in ["wake up", "wake-up", "எழுந்திரு", "எழும்பு"]):
                        state_machine.set_state(LIAState.LISTENING)
                        logger.info(f"[WAKEWORD][{cmd_id}] Waking up from sleep mode.")
                        logger.info(f"[LIVEKIT][{cmd_id}] Listening state active")
                        conv_manager.add_user_message(transcript)
                        loop = asyncio.get_running_loop()
                        loop.create_task(session.generate_reply(instructions="Speak warmly: 'I am awake and listening, boss. How can I help you?'"))
                        return
                    else:
                        logger.info(f"[WAKEWORD][{cmd_id}] LIA is sleeping. Ignoring transcript: {transcript}")
                        return

                # Check for sleep command in ACTIVE mode
                if any(s in t_lower for s in ["sleep", "go to sleep", "stop listening", "தூங்கு"]):
                    state_machine.set_state(LIAState.SLEEPING)
                    logger.info(f"[WAKEWORD][{cmd_id}] Entering sleep mode.")
                    logger.info(f"[LIVEKIT][{cmd_id}] Sleeping state active")
                    conv_manager.add_user_message(transcript)
                    loop = asyncio.get_running_loop()
                    loop.create_task(session.generate_reply(instructions="Speak warmly: 'Going to sleep, boss. Say LIA wake up whenever you need me.'"))
                    return

                # Normal ACTIVE Command Pipeline
                state_machine.set_state(LIAState.PROCESSING)
                decision = wakeword_detector.process_transcript(transcript)
                cleaned_prompt = decision.get("cleaned_prompt") or transcript
                logger.info(f"[WAKEWORD][{cmd_id}] Wake word check: activated={decision.get('activated')}, prompt='{cleaned_prompt}'")
                
                if decision.get("is_interruption"):
                    logger.info(f"[WAKEWORD][{cmd_id}] User interrupted LIA response.")

                conv_manager.add_user_message(transcript)

                # Classify intent and execute orchestrator pipeline for speech command
                intent = orchestrator.classify_intent(cleaned_prompt)
                logger.info(f"[COMMAND][{cmd_id}] Cleaned payload: '{cleaned_prompt}'")
                logger.info(f"[ORCHESTRATOR][{cmd_id}] Intent classified: {intent.get('primary_intent')} (Target: {intent.get('target_device')})")

                try:
                    loop = asyncio.get_running_loop()
                    task = loop.create_task(orchestrator.process_request(cleaned_prompt))
                    
                    def _on_orch_done(fut):
                        try:
                            res = fut.result()
                            logger.info(f"[TOOL][{cmd_id}] Action result: {res}")
                            if res and res.get("status") == "success":
                                msg = res.get("message", "Action completed.")
                                logger.info(f"[AUDIO-OUT][{cmd_id}] Generating audio reply for action: {msg}")
                                prompt = f"The user said '{transcript}'. LIA Orchestrator executed action: {msg}. Provide a concise, natural spoken answer back to the user."
                                loop.create_task(session.generate_reply(instructions=prompt))
                        except Exception as o_err:
                            logger.error(f"[ERROR][{cmd_id}] Orchestrator execution error: {o_err}")

                    task.add_done_callback(_on_orch_done)
                except Exception as loop_err:
                    logger.warning(f"[ERROR][{cmd_id}] Event loop dispatch note: {loop_err}")

        @session.on("speech_created")
        def on_speech_created(ev):
            if hasattr(ev, "text") and ev.text:
                logger.info(f"[TTS] Gemini Realtime audio synthesized: {ev.text}")
                logger.info("[AUDIO-OUT] Audio published to LiveKit room track")
                state_machine.set_state(LIAState.SPEAKING)
                conv_manager.add_assistant_message(ev.text)
                
                # Automatically return to LISTENING state after response finishes
                def _return_to_listening():
                    import time as _t
                    _t.sleep(1.0)
                    if state_machine.get_state() == LIAState.SPEAKING:
                        state_machine.set_state(LIAState.LISTENING)
                        logger.info("[LIVEKIT] State returned to Listening")

                import threading as _th
                _th.Thread(target=_return_to_listening, daemon=True).start()

        # Attempt noise cancellation if available, fallback gracefully
        room_options = None
        try:
            room_options = room_io.RoomOptions(
                audio_input=room_io.AudioInputOptions(
                    noise_cancellation=ai_coustics.audio_enhancement(
                        model=ai_coustics.EnhancerModel.QUAIL_VF_S
                    ),
                )
            )
        except Exception as n_err:
            logger.warning(f"[AUDIO-IN] Noise cancellation initialization note: {n_err}")

        # Start the Agent Session
        if room_options:
            await session.start(room=ctx.room, agent=Assistant(), room_options=room_options)
        else:
            await session.start(room=ctx.room, agent=Assistant())

        logger.info("[BOOT] LIA Unified JARVIS Agent Session started successfully.")
        state_machine.set_state(LIAState.CONNECTED)
        state_machine.set_state(LIAState.LISTENING)
        logger.info("[LIVEKIT] State set to LISTENING")

        await session.generate_reply(instructions=INITIAL_GREETING_PROMPT)

    except Exception as e:
        state_machine.set_state(LIAState.ERROR)
        logger.error(f"[ERROR] Exception during LIA agent session: {e}", exc_info=True)


if __name__ == "__main__":
    # Launch Mobile HTTP Token & Telemetry Server on Port 8080
    try:
        m_port = int(os.getenv("PORT", "8080"))
        run_mobile_server(port=m_port, daemon=True)
        logger.info(f"[BOOT] Mobile HTTP Backend Server running on 0.0.0.0:{m_port}")
    except Exception as m_err:
        logger.warning(f"[BOOT] Mobile server auto-start warning: {m_err}")
        
    # Default argument fallback for LiveKit CLI runner if executed without parameters
    if len(sys.argv) == 1:
        sys.argv.append("dev")

    agents.cli.run_app(server)