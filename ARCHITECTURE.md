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
│   └── projects.py             # Coding project tools
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

No restart required.

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
