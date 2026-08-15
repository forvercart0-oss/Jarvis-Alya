# Architecture

## System Overview

JARVIS 2.0 is a multi-process desktop application:

1. **Tauri Window** — Native OS window rendering the React frontend.
2. **FastAPI Backend** — Python async server handling AI, voice, tools, memory, and system operations.
3. **Worker Processes** — Kokoro TTS runs in a persistent subprocess to avoid GIL/import conflicts.

Communication flows over **WebSocket** (`/ws/jarvis`) for real-time events and **REST** (`/api/*`) for requests.

## Directory Layout

```
Jarvis2.0/
├── backend/
│   ├── main.py                 # FastAPI app + lifespan
│   ├── api/                    # REST routers
│   │   ├── chat.py
│   │   ├── voice.py
│   │   ├── system.py
│   │   ├── memory.py
│   │   ├── settings.py
│   │   ├── tools.py
│   │   ├── automation.py
│   │   └── persona.py
│   └── services/               # Backend services
│       ├── ai_service.py       # AI orchestration + streaming
│       ├── voice_service.py    # Voice manager facade
│       ├── ws_manager.py       # WebSocket connection manager
│       ├── system_service.py   # psutil + platform stats
│       ├── persona_service.py  # JARVIS/ALYA switching
│       ├── memory_service.py   # Memory CRUD
│       ├── tool_service.py     # Tool execution wrapper
│       ├── automation_service.py
│       └── notification_service.py
├── brain/
│   ├── provider.py             # Abstract AI provider
│   ├── provider_registry.py    # Provider factory + selection
│   ├── groq_provider.py        # Groq implementation
│   ├── gemini_provider.py      # Gemini implementation
│   ├── openrouter_provider.py  # OpenRouter implementation
│   ├── local_provider.py       # Ollama / OpenAI-compatible
│   ├── router.py               # Heuristic tool routing
│   ├── conversation.py         # Conversation history manager
│   ├── prompts.py              # System prompt builder
│   └── offline.py              # Offline fallback replies
├── voice/
│   ├── __init__.py             # VoiceService facade
│   ├── tts_manager.py          # Async TTS queue + engine routing
│   ├── kokoro_tts.py           # Kokoro implementation (worker/python/espeak)
│   ├── tts.py                  # espeak-ng fallback
│   ├── listener.py             # Microphone recorder
│   ├── recognizer.py           # STT (Google/Vosk)
│   └── wakeword.py             # Wake word detection
├── tools/
│   ├── registry.py             # ToolRegistry + build_registry()
│   ├── terminal.py             # Shell execution + danger checks
│   ├── filesystem.py           # Read/Write/Delete files
│   ├── system.py               # CPU/RAM/Disk/Battery/Volume/Brightness
│   ├── applications.py         # Open/close apps
│   ├── browser.py              # Open browser URLs
│   ├── web.py                  # Web search
│   ├── screen.py               # Screenshot + input
│   ├── calculator.py           # Math evaluation
│   ├── time.py                 # Time/date
│   ├── memory_tools.py         # Remember/forget/recall
│   ├── projects.py             # Coding project tools
│   └── media.py                # Image/video generation tools
├── generation/
│   ├── image/
│   │   ├── provider.py         # Abstract image provider
│   │   ├── manager.py          # Image generation manager
│   │   ├── puter_provider.py   # Puter (free)
│   │   ├── pixazo_provider.py  # Pixazo (free tier)
│   │   └── gemini_provider.py  # Gemini
│   └── video/
│       ├── provider.py         # Abstract video provider
│       ├── manager.py          # Video generation manager
│       ├── fal_provider.py     # fal.ai
│       └── magic_hour_provider.py # Magic Hour
├── vision/
│   └── gesture/
│       ├── detector.py         # Gesture detection (local CV)
│       ├── gestures.py         # Gesture definitions
│       └── controller.py       # Gesture-to-action mapping
├── communications/
│   └── calls/
│       ├── provider.py         # Abstract call provider
│       ├── manager.py          # Call control manager
│       └── permissions.py      # Call permission levels
├── system/
│   ├── base.py                 # Abstract platform interface
│   ├── linux.py                # Linux implementations
│   ├── windows.py              # Windows implementations
│   └── macos.py                # macOS implementations
├── computer/
│   ├── controller.py           # Unified computer control
│   └── input.py                # Keyboard + mouse
├── config/
│   ├── settings.py             # Pydantic settings + persistence
│   ├── personas.py             # JARVIS/ALYA definitions
│   └── prompts.py              # Legacy prompt builder
├── memory/
│   ├── manager.py              # MemoryManager facade
│   ├── store.py                # SQLite store
│   ├── sqlite_memory.py        # SQLite implementation
│   └── vector_memory.py        # ChromaDB implementation
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # Root component + layout
│   │   ├── components/         # React components
│   │   ├── hooks/              # useJarvis, useSettings, etc.
│   │   ├── services/           # API + WebSocket clients
│   │   ├── types/              # TypeScript interfaces
│   │   └── styles/             # Tailwind + globals
│   └── dist/                   # Production build output
├── src-tauri/                  # Tauri Rust shell
│   ├── src/
│   │   ├── lib.rs
│   │   └── main.rs
│   ├── Cargo.toml
│   └── tauri.conf.json
├── data/                       # SQLite DB (gitignored)
├── logs/                       # Log files (gitignored)
├── main.py                     # Backend entry point
├── run.sh                      # Dev / desktop launcher
├── install.sh                  # System setup script
└── pyproject.toml              # Python tooling config
```

## Data Flow: Chat

```
User types / speaks
        │
        ▼
Frontend (WebSocket /api/chat)
        │
        ▼
AIService.process_message()
        │
        ├── Router.heuristic_route() → tool call?
        │
        ├── Provider.chat_with_tools() → streaming
        │       │
        │       ├── Tool execution (with confirmation flow)
        │       │
        │       └── Final text response
        │
        ▼
WebSocket events → frontend
        │
        ├── thinking
        ├── token (streamed chunks)
        ├── tool_start / tool_result
        ├── speaking
        └── done
        │
        ▼
TTSManager.speak_chunks() → Kokoro → PipeWire
```

## Data Flow: Voice

```
Microphone
    │
    ▼
Listener.record() [thread]
    │
    ▼
Recognizer.recognize() [thread]
    │
    ▼
AIService.process_message()
    │
    ▼
Streaming response → WebSocket
    │
    ▼
TTSManager.speak_chunks()
    │
    ▼
KokoroTTS.render() → WAV → pw-play
```

## Provider Selection

Priority is configurable via `provider_priority`:

- `groq_first` → Groq → any available
- `local_first` → Local LLM → any available
- `auto` → Local → Groq → Gemini → OpenRouter
- `groq_only` / `local_only` / `gemini_only` / `openrouter_only`

On failure, `auto_failover` walks the remaining providers.

## Tool Permission Levels

| Level | Behavior |
|-------|----------|
| SAFE | Executes without confirmation |
| LOW_RISK | Executes, logs action |
| CONFIRM | Blocks until user confirms via WebSocket |
| BLOCKED | Rejected outright |

Dangerous patterns (`rm -rf`, `mkfs`, `dd`, `shutdown`, etc.) are mapped to CONFIRM or BLOCKED.

## Persona System

Personas are defined in `config/personas.py` as frozen dataclasses. Switching:

1. Updates `settings.persona`, `settings.assistant_name`, `settings.accent_color`, `settings.tts_voice`.
2. Persists to `.env` and SQLite settings store.
3. Applies TTS voice change live via `tts_manager.set_voice()`.
4. Broadcasts `persona_switched` WebSocket event.
5. Next AI request uses the new persona's system prompt (masculine/feminine grammar enforced at prompt layer).

Greeting rule is part of the persona prompt:
- JARVIS: "Assalamualaikum. Main JARVIS hoon. Aap kaise hain?"
- ALYA: "Assalamualaikum. Main ALYA hoon. Aap kaise hain?"

No restart required.

## Language System

Language detection lives in `language/detector.py`. It detects:
- English
- Urdu (Perso-Arabic script)
- Roman Urdu (Latin-script Urdu)
- Hinglish / mixed

The response style is determined per-message and injected into the system prompt. No post-hoc string replacement is used.

## Media Generation

### Image
- Abstraction: `generation/image/provider.py`
- Manager: `generation/image/manager.py`
- Providers: Puter (free), Pixazo (free tier), Gemini (paid)
- Router detects intents like "generate an image", "create a wallpaper", "image banao"

### Video
- Abstraction: `generation/video/provider.py`
- Manager: `generation/video/manager.py`
- Providers: fal.ai (paid), Magic Hour (paid)
- Router detects intents like "generate a video", "make a cinematic video", "video banao"

## Gesture Control

- Detection: `vision/gesture/detector.py`
- Definitions: `vision/gesture/gestures.py`
- Controller: `vision/gesture/controller.py`

Gestures run locally. Camera is OFF by default. When enabled, a visible indicator is shown. Dangerous actions require confirmation.

## Call Control

- Provider abstraction: `communications/calls/provider.py`
- Manager: `communications/calls/manager.py`
- Permissions: `communications/calls/permissions.py`

Only legitimate supported interfaces are used. No bypassing of security or platform restrictions.

## Update System (Planned)

The updater will:

1. Query GitHub Releases API for the current channel.
2. Compare semver with `tauri.conf.json` version.
3. Download the platform-specific artifact (AppImage / deb / exe / dmg).
4. Verify signature if available.
5. Replace the binary while preserving `data/`, `.env`, and `logs/`.
6. Restart the application.

## Cross-Platform Strategy

OS-specific code lives in `system/linux.py`, `system/windows.py`, `system/macos.py` behind `system/base.py`. The frontend is platform-agnostic. Tauri handles windowing differences.
