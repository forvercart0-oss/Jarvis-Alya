# JARVIS 2.0

A production-quality, cross-platform desktop AI assistant built with Tauri, React, FastAPI, and Python.

## Features

- **Native Desktop App** — No browser required. Tauri-powered window with frameless HUD UI.
- **AI Providers** — Groq (default), Gemini, OpenRouter, Local LLM (Ollama/OpenAI-compatible).
- **Voice Pipeline** — Kokoro TTS with low-latency streaming, Google STT, wake word support.
- **Personas** — Switch between JARVIS (male/cyan) and ALYA (female/pink) at runtime.
- **System Control** — Real CPU/RAM/disk/battery/network monitoring, app launching, terminal execution.
- **Computer Use** — Screenshots, keyboard/mouse input, browser automation, accessibility-aware interaction.
- **Coding Agent** — Project inspection, file creation/editing, full-stack scaffolding.
- **Memory** — SQLite conversations + optional ChromaDB vector memory.
- **Automations** — Scheduled tasks with persistence.
- **WebSocket** — Real-time streaming chat with reconnect, heartbeat, and tool events.

## Architecture

```
Tauri (Rust)
  └── React / TypeScript frontend
        └── WebSocket / REST → FastAPI backend
              ├── AI providers (Groq, Gemini, OpenRouter, Local)
              ├── Voice services (Kokoro TTS, Google STT)
              ├── System tools (psutil, subprocess)
              ├── Computer control (input, screenshots, browser)
              ├── Memory (SQLite + ChromaDB)
              └── Automations + Notifications
```

## Requirements

- Python 3.11+
- Node.js 18+
- npm 9+
- Rust 1.70+ (for Tauri desktop build)
- Arch Linux recommended (Linux-first design)

## Quick Start

```bash
# 1. Clone
git clone https://github.com/forvercart0-oss/Jarvis-Alya.git
cd Jarvis-Alya

# 2. Install dependencies
./install.sh

# 3. Configure
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# 4. Run
./run.sh
```

Or launch from your application menu after installation: **JARVIS 2.0**

## Configuration

### AI Providers

| Provider | Env Vars | Notes |
|----------|----------|-------|
| Groq | `GROQ_API_KEY`, `GROQ_MODEL` | Default, fastest |
| Gemini | `GEMINI_API_KEY`, `GEMINI_MODEL` | Optional |
| OpenRouter | `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` | Optional, free models available |
| Local LLM | `LOCAL_LLM_ENABLED`, `LOCAL_LLM_URL`, `LOCAL_LLM_MODEL` | Ollama or OpenAI-compatible |

### Voice

| Setting | Env Var | Default |
|---------|---------|---------|
| TTS Engine | `TTS_ENGINE` | `kokoro` |
| Voice | `TTS_VOICE` | `af_heart` |
| Speed | `TTS_SPEED` | `150` |
| Volume | `TTS_VOLUME` | `80` |
| STT Engine | `STT_ENGINE` | `google` |
| Wake Word | `WAKE_WORD` | `Hey JARVIS` |
| Wake Word Enabled | `WAKE_WORD_ENABLED` | `true` |

### Personas

| Persona | Gender | Accent | Voice | Grammar |
|---------|--------|--------|-------|---------|
| JARVIS | Male | `#00f0ff` | `am_fenrir` | Masculine Urdu/Hinglish |
| ALYA | Female | `#ff6ec7` | `af_heart` | Feminine Urdu/Hinglish |

Switch dynamically from Settings → Persona or the sidebar button. No restart required.

## Development

```bash
# Backend only
source .venv/bin/activate
python main.py

# Frontend dev server
cd frontend
npm run dev

# Tauri dev (desktop window)
npm run tauri:dev

# Build frontend for production
npm run build

# Build Tauri desktop app
npm run tauri:build
```

## Production Build (Linux)

```bash
# Install system dependencies for Tauri
sudo pacman -S --needed webkit2gtk-4.1 libappindicator-gtk3 librsvg libxdo openssl base-devel cmake patchelf pkg-config

# Build desktop application
npm run tauri:build

# Binary will be in:
# src-tauri/target/release/bundle/appimage/
# src-tauri/target/release/bundle/deb/
```

## Security

See [SECURITY.md](SECURITY.md) for API key handling, secrets management, and tool permission levels.

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — System design and module layout
- [SECURITY.md](SECURITY.md) — Security policies and best practices

## Troubleshooting

### Backend won't start
```bash
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Tauri build fails
Ensure `webkit2gtk-4.1` and related system packages are installed (see Production Build above).

### Kokoro TTS not working
Kokoro requires a dedicated virtualenv on Python 3.11/3.12. Set `TTS_VENV_DIR` to the path of a venv with `kokoro` installed, or use `espeak-ng` fallback (`TTS_ENGINE=espeak-ng`).

### Microphone unavailable
```bash
pactl list sources short
arecord -l
```

## License

MIT
