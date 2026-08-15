# JARVIS 2.0

A production-quality, cross-platform desktop AI assistant built with Tauri, React, FastAPI, and Python.

## Features

- **Native Desktop App** — No browser required. Tauri-powered window with frameless HUD UI.
- **AI Providers** — Groq (default), Gemini, OpenRouter, Local LLM (Ollama/OpenAI-compatible).
- **Voice Pipeline** — Kokoro TTS with low-latency streaming, Google STT, wake word support.
- **Personas** — Switch between JARVIS (male/cyan) and ALYA (female/pink) at runtime.
- **Language** — Auto-detect English, Urdu, Roman Urdu, Hinglish. Responds in the user's language style.
- **Image Generation** — Puter (free), Pixazo (free tier), Gemini.
- **Video Generation** — fal.ai, Magic Hour.
- **Gesture Control** — Hand gesture recognition via local computer vision (configurable).
- **Call Control** — Legitimate call provider integration with permission controls.
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

## Installation

Choose your OS and copy-paste the commands.

### Arch Linux

```bash
sudo pacman -S --needed python3 python-pip python-virtualenv nodejs npm webkit2gtk-4.1 libappindicator-gtk3 librsvg xdotool openssl base-devel cmake patchelf pkg-config
git clone https://github.com/forvercart0-oss/Jarvis-Alya.git
cd Jarvis-Alya
./install.sh
```

### Debian / Ubuntu

```bash
sudo apt install python3 python3-pip python3-venv nodejs npm libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev libxdo-dev libssl-dev libayatana-appindicator3-dev pkg-config build-essential
git clone https://github.com/forvercart0-oss/Jarvis-Alya.git
cd Jarvis-Alya
./install.sh
```

### Fedora

```bash
sudo dnf install python3 python3-pip nodejs npm webkit2gtk4-devel libappindicator-gtk3-devel librsvg2-devel xdotool openssl-devel cmake pkg-config
git clone https://github.com/forvercart0-oss/Jarvis-Alya.git
cd Jarvis-Alya
./install.sh
```

### macOS

```bash
brew install python node webkit2gtk-4.1 libappindicator-gtk3 librsvg xdotool openssl cmake pkg-config
git clone https://github.com/forvercart0-oss/Jarvis-Alya.git
cd Jarvis-Alya
./install-macos.sh
```

### Windows (PowerShell as Administrator)

```powershell
winget install Python.Python.3.12 OpenJS.NodeJS.LTS Git.Git
git clone https://github.com/forvercart0-oss/Jarvis-Alya.git
cd Jarvis-Alya
.\install-windows.ps1
```

## Post-Install Configuration

After installation:

```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

Run with `./run.sh` (Linux/macOS) or `.\run.bat` (Windows), or launch **JARVIS 2.0** from your application menu.

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

## Building Desktop App

```bash
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
Ensure `webkit2gtk-4.1` and related system packages are installed (see Installation above).

### Kokoro TTS not working
Kokoro requires a dedicated virtualenv on Python 3.11/3.12. Set `TTS_VENV_DIR` to the path of a venv with `kokoro` installed, or use `espeak-ng` fallback (`TTS_ENGINE=espeak-ng`).

### Microphone unavailable
```bash
pactl list sources short
arecord -l
```

## License

MIT
