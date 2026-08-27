# LIA Voice System

This module manages the voice processing pipeline for LIA using LiveKit.

## Architecture

```text
Microphone (User Audio)
       ↓
LiveKit WebRTC Connection
       ↓
Python LIA Agent (agent.py)
       ↓
Speech-to-Text / Audio Processing
       ↓
AI / LLM (Gemini 2.5/3.6 Flash Native Audio / Google LLM)
       ↓
Text-to-Speech / Voice Output
       ↓
Speaker (User Audio Output)
```

## Features

- **Multilingual Recognition**: Understood inputs in English, Tamil, and Tanglish.
- **Audio Processing & Noise Cancellation**: Compatible with `ai_coustics` or standard noise-suppression plugins.
- **Realtime Conversational Turn-Taking**: Low-latency voice streaming via LiveKit AgentSession.

## Testing Voice Interaction

1. Launch `agent.py dev` on the local machine.
2. Connect to the LiveKit Sandbox or frontend client using your `LIVEKIT_URL` and tokens.
3. Speak into your microphone in English, Tamil, or Tanglish.
4. LIA will process your audio and respond back over speaker in the matching language.
