# LIA - Final Unified AI Voice Assistant (Phases 1–8 Complete)

LIA is a complete, unified personal AI voice assistant built with Python, LiveKit Cloud WebRTC streaming, Google Gemini Multimodal Audio & Vision AI, Mobile Device Integration, Central Tool Orchestration, and Security Engine.

In **Phase 7** and **Phase 8**, LIA adds **Mobile Device Integration (Android/iOS Client & Secure Token Server)**, **Unified Device Registry**, **Central Tool & Action Orchestrator**, **Wake Word Detection System ("Hey LIA")**, **Multi-Step Task Execution**, **Security Permission & High-Risk Guard Engine**, and **Unified Multilingual Memory** across Desktop and Mobile in **English**, **Tamil**, and **Tanglish (Tamil-English mixed speech)**.

---

## 1. Complete Architecture

```text
                                USER
                                 │
                   Voice / Text (English, Tamil, Tanglish)
                                 │
                     ┌───────────┴───────────┐
                     │                       │
                  DESKTOP                 MOBILE
             (Python Agent Session)  (Mobile App Client)
                     │                       │
                     └───────────┬───────────┘
                                 │
                              LIVEKIT
                                 │
                         LIA BRAIN AGENT
                                 │
                 Central Orchestrator & Safety Layer
               (security/permissions.py, validation.py)
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
     AI BRAIN               WEB SEARCH              DEVICE MATRIX
 (Gemini Realtime)       (tools/web_search)    ┌──────────┴──────────┐
        │                        │             │                     │
        │                        │          DESKTOP               MOBILE
        │                        │    (tools/desktop,       (tools/mobile,
        │                        │     screen, mouse,       devices/registry)
        │                        │     keyboard, system)         │
        └────────────────────────┴─────────────┬─────────────────┘
                                               │
                                       UNIFIED MEMORY
                                  (SQLite persistent db)
```

---

## 2. Capability Matrix (Phases 1–8)

| Category | Features & Tools | Description |
| :--- | :--- | :--- |
| **Multilingual Voice** | English, Tamil (தமிழ்), Tanglish | Seamless code-switching and response matching with English technical terms preserved. |
| **Mobile Integration** | Mobile App, Token Server, Device Status | Cross-platform mobile UI (`mobile/app/index.html`), secure token API (`/api/mobile/token`), battery telemetry sync (`/api/mobile/status`). |
| **Device Management** | Central Device Registry (`devices/registry.py`) | Real-time device registration, online/offline tracking, battery telemetry, and target normalization ("laptop" vs "phone"). |
| **Central Orchestrator** | Intent Classifier, Multi-Step Executor (`brain/orchestrator.py`) | Natural intent routing into AI, Web, Desktop, Mobile, Memory, and compound multi-step task decomposition. |
| **Wake Word System** | Keyword Detector & Conversation Modes (`voice/wakeword.py`) | Supports `"Hey LIA"`, `"LIA"`, conversation modes (`ACTIVE`, `ONE_SHOT`, `WAKE_WORD`, `PUSH_TO_TALK`), and voice interruption handling. |
| **Security Layer** | Permission Engine & Secret Masker (`security/`) | Validates parameters, masks secrets in logs (`LIVEKIT_API_SECRET`, API keys), blocks dangerous commands, and safeguards high-risk actions. |
| **Unified Memory** | Persistent SQLite Storage (`memory/`) | Remembers preferences, facts, reminders, and context across desktop and mobile sessions. |
| **Desktop Automation** | Application & Folder Control (`tools/desktop.py`, `browser.py`) | Launch/close allowed apps (Chrome, VS Code, Notepad, Calc, Explorer) and safe folders (Downloads, Documents). |
| **Vision & Screen** | Multimodal Screen Understanding (`tools/screen.py`) | Capture screenshots and analyze visible UI buttons, text, and active windows using Gemini Vision. |
| **Mouse & Keyboard** | Controlled System Automation (`tools/mouse.py`, `keyboard.py`) | Click, double-click, right-click, move cursor, type text, and execute keyboard hotkeys (`Ctrl+C`, `Ctrl+V`). |

---

## 3. Installation & Environment Setup

### 1. Clone & Setup Virtual Environment
```powershell
cd "c:\Projects\LIA 5.0"
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables (`.env`)
Copy `.env.example` to `.env` and fill in credentials:
```env
# LiveKit Cloud Configuration
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

# AI Provider Configuration
GOOGLE_API_KEY=your_google_gemini_api_key
```

> **Security Note**: Never expose or embed `LIVEKIT_API_SECRET` inside mobile client applications. The mobile application retrieves short-lived JWT tokens from the secure backend.

---

## 4. Running LIA Assistant & Mobile Client

### Option A: Run LIA Agent Server
```powershell
.\venv\Scripts\python.exe agent.py dev
```
This automatically initializes the **Desktop Device Entry** in the DeviceRegistry and launches the **Mobile Token Backend Server** on `http://localhost:8080/`.

### Option B: Mobile Web Client
Open your mobile browser or desktop browser to:
```text
http://localhost:8080/
```
The mobile application will:
1. Connect to the LiveKit server securely via `/api/mobile/token`.
2. Display connection status, microphone visualizer, and conversation transcript.
3. Automatically sync mobile battery and network telemetry to LIA's DeviceRegistry via `/api/mobile/status`.

---

## 5. Automated Test Suite

To run all 29 automated tests covering Phase 1 through Phase 8:

```powershell
.\venv\Scripts\pytest.exe tests/
```

Test files included:
- `tests/test_all_tools.py`: System telemetry, browser control, and tool registration.
- `tests/test_phase5_phase6.py`: Vision screen capture, mouse, keyboard, and persistent SQLite memory.
- `tests/test_phase7_phase8.py`: Security engine, device registry, mobile token generation, mobile HTTP server, mobile tools, central orchestrator, wake-word detector, and unified multilingual memory.

---

## 6. Security & Safety Model

LIA enforces strict security policies prior to executing any tool:
- **No Arbitrary Shell Execution**: All system operations use strict allowlists (`APPLICATION_ALLOWLIST`, `FOLDER_ALLOWLIST`).
- **High-Risk Guard**: System formatting (`format_disk`), system file deletion, system shutdown, and credential changes are blocked or require explicit user confirmation.
- **Secret Protection**: `LIVEKIT_API_SECRET`, `GOOGLE_API_KEY`, and bearer tokens are automatically masked from response logs and output text.
- **Credential Storage Safeguard**: Persistent memory automatically rejects storing passwords, secrets, or API keys.

---

## 7. Project Structure

```text
LIA/
│
├── agent.py               # Main LiveKit Agent entrypoint, server registration & agent session
├── requirements.txt       # Project dependencies
├── .env                   # Environment secrets (Git protected)
├── .env.example           # Environment template
├── README.md              # Project documentation
│
├── brain/
│   ├── prompts.py         # System prompt instructions for Phase 1-8 capabilities
│   ├── conversation.py    # Turn history & conversation context manager
│   └── orchestrator.py    # Central Orchestrator & Intent Routing Engine
│
├── devices/
│   ├── registry.py        # Central DeviceRegistry singleton (Desktop & Mobile state)
│   ├── desktop.py         # Desktop device representation & telemetry sync
│   └── mobile.py          # Mobile device representation & push notification helper
│
├── mobile/
│   ├── server.py          # HTTP Token & Telemetry server (Port 8080)
│   └── app/
│       └── index.html     # Responsive Glassmorphism LIA Mobile Web UI
│
├── security/
│   ├── permissions.py     # Permission levels, safety checks & high-risk action guards
│   └── validation.py      # Parameter validator & secret masking engine
│
├── voice/
│   ├── wakeword.py        # "Hey LIA" wake word detector & conversation modes
│   └── audio.py           # Audio energy VAD & noise cancellation helper
│
├── memory/
│   ├── database.py        # SQLite persistent database schema & connection
│   ├── manager.py         # Memory CRUD operations & credential filter
│   └── retrieval.py       # Memory formatting & retrieval engine
│
├── tools/
│   ├── __init__.py        # Exports ALL_LIA_TOOLS
│   ├── web_search.py      # Real-time DuckDuckGo web search
│   ├── desktop.py         # Application & folder control
│   ├── browser.py         # Website shortcut launcher
│   ├── system.py          # CPU, RAM, Disk, Battery system telemetry
│   ├── screen.py          # Screenshot capture & Gemini Vision screen analysis
│   ├── mouse.py           # Mouse movement & clicking
│   ├── keyboard.py        # Text typing & keyboard hotkeys
│   ├── memory_tools.py    # Long-term memory tools
│   └── mobile.py          # Mobile telemetry, notification, & device list tools
│
└── tests/
    ├── test_all_tools.py        # System, browser, & search unit tests
    ├── test_phase5_phase6.py   # Screen vision, mouse, keyboard, & memory tests
    └── test_phase7_phase8.py   # Security, device registry, mobile server, orchestrator, & wake word tests
```
