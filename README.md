# JARVIS / ALYA

<p align="center">
  <img src="assets/logo.svg" alt="JARVIS / ALYA" width="320" />
</p>

<p align="center">
  <strong>An advanced open-source AI desktop assistant built for conversation, automation, coding, research, voice, computer control, and intelligent workflows.</strong>
</p>

<p align="center">
  <a href="https://github.com/forvercart0-oss/Jarvis-Alya"><img alt="GitHub" src="https://img.shields.io/badge/GitHub-forvercart0--oss%2FJarvis--Alya-black?logo=github"></a>
  <a href="https://opensource.org/licenses/MIT"><img alt="License" src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>
  <img alt="Platform" src="https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11%2B-blue?logo=python">
  <img alt="Node" src="https://img.shields.io/badge/Node.js-18%2B-green?logo=node.js">
  <img alt="Rust" src="https://img.shields.io/badge/Rust-1.70%2B-orange?logo=rust">
  <img alt="Tests" src="https://img.shields.io/badge/Tests-773%20passing-brightgreen">
</p>

---

## Download & Install

JARVIS requires **Python 3.11+**, **Node.js 18+**, and **Rust 1.70+** (for the desktop app). Select your platform:

### Linux

```bash
# Arch Linux
sudo pacman -S --needed python3 python-pip python-virtualenv nodejs npm \
  webkit2gtk-4.1 libappindicator-gtk3 librsvg xdotool openssl base-devel cmake patchelf pkg-config appmenu-gtk-module

# Debian / Ubuntu
sudo apt install -y python3 python3-pip python3-venv nodejs npm \
  libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev libxdo-dev \
  libssl-dev libayatana-appindicator3-dev pkg-config build-essential

# Fedora
sudo dnf install -y python3 python3-pip nodejs npm \
  webkit2gtk4-devel libappindicator-gtk3-devel librsvg2-devel \
  xdotool openssl-devel cmake pkgconfig

# Clone and install
git clone https://github.com/forvercart0-oss/Jarvis-Alya.git
cd Jarvis-Alya
./install.sh

# Run
./run.sh
```

The installer sets up a Python virtualenv, installs Python and Node dependencies, builds the frontend, creates a desktop launcher, and configures Tauri. Launch JARVIS from your application menu or run `./run.sh` for development mode.

### macOS

```bash
brew install python node cmake pkg-config

git clone https://github.com/forvercart0-oss/Jarvis-Alya.git
cd Jarvis-Alya
./install-macos.sh

# Run
./run-macos.sh
```

### Windows

Run **PowerShell as Administrator**:

```powershell
# Install dependencies
winget install Python.Python.3.12 OpenJS.NodeJS.LTS Git.Git

# Clone and install
git clone https://github.com/forvercart0-oss/Jarvis-Alya.git
cd Jarvis-Alya
.\install-windows.ps1

# Run
.\run.bat
```

The Windows installer configures Python, Node.js, Rust, Tauri dependencies, and creates desktop/start menu shortcuts.

---

## Quick Start

```bash
# After installation
cp .env.example .env
# Edit .env and add your API keys (see Configuration below)

./run.sh           # Linux / macOS
.\run.bat          # Windows
```

---

## What Can JARVIS Do?

### Dual Personas: JARVIS & ALYA

Switch between two distinct AI personalities at runtime — no restart required.

| Persona | Voice | Theme | Style |
|---------|-------|-------|-------|
| **JARVIS** | Male (`am_fenrir`) | Cyan (`#00f0ff`) | Direct, technical |
| **ALYA** | Female (`af_heart`) | Pink (`#ff6ec7`) | Warm, conversational |

Switch via the sidebar persona button or Settings → Persona.

### Multi-Provider AI

Connect to any combination of AI providers with automatic failover:

| Provider | Notes | Env Vars |
|----------|-------|----------|
| **Groq** | Default, lowest latency | `GROQ_API_KEY`, `GROQ_MODEL` |
| **Gemini** | Google Gemini models | `GEMINI_API_KEY`, `GEMINI_MODEL` |
| **OpenRouter** | Access to many free-tier models | `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` |
| **Local LLM** | Ollama or OpenAI-compatible | `LOCAL_LLM_ENABLED`, `LOCAL_LLM_URL`, `LOCAL_LLM_MODEL` |

### Voice Pipeline

Full-duplex voice interaction:

- **Text-to-Speech**: Kokoro TTS with low-latency streaming; espeak-ng fallback
- **Speech-to-Text**: Google STT
- **Wake Word**: Configurable detection (default: "Hey JARVIS")
- **Settings**: Adjustable speed, volume, voice selection per persona

### Real-Time Chat

- WebSocket streaming with tool call visualization
- Conversation history with search
- Offline mode when the backend is unreachable
- Automatic reconnection with heartbeat

### Computer Control

Interact with your computer through a permission-gated system:

- **Screen**: Screenshot capture, screen info, accessibility tree
- **Input**: Keyboard and mouse control (with safety guards)
- **Applications**: Launch and switch between apps
- **Terminal**: Execute shell commands with approval workflows
- **Processes**: List and manage running processes
- **Clipboard**: Read and write clipboard content
- **Windows**: List, focus, and manipulate windows

### Browser Automation

Playwright-powered browser automation:

- Navigate, fill forms, click elements, read content
- Session persistence across tasks
- Browser memory and state recovery
- Anti-loop protection

### Coding Agent

- Project inspection and file indexing
- Create, edit, and refactor files
- Full-stack scaffolding
- Git integration (status, log, diff)
- Multi-agent coordination for complex goals

### Research

Deep research pipeline with:

- Web search and source extraction
- Document parsing and analysis
- Claim verification and cross-referencing
- Research job tracking with full history
- Document export

### Image & Video Generation

| Type | Providers |
|------|-----------|
| Images | Puter (free), Pixazo (free tier), Gemini |
| Video | fal.ai, Magic Hour |

Generated media is saved to `data/generated/`.

### Memory System

- **Conversations**: SQLite-backed persistent storage
- **Vector Memory**: Optional ChromaDB semantic search with local embeddings
- **Project Memory**: Per-project context isolation
- **Adaptive Preferences**: Learning from explicit and inferred user behavior
- **Memory Decay**: Automatic importance decay and cleanup
- **Export/Import**: Full backup and restore

### Skills

- Built-in skills from `skills/builtin/`
- Custom skills from `skills/custom/`
- Skill validation and sandboxing
- Import/export packages
- Priority-based activation routing

### Workflows & Automations

- Multi-step workflow definitions with conditional branching
- Approvals for sensitive operations
- Scheduled tasks with persistence
- Scope-based permissions (files, terminal, browser, applications, system, etc.)
- Retry logic and backoff

### Goals & Multi-Agent System

- Goal decomposition engine — high-level goals broken into task graphs
- Specialized agent registry: Research, Coding, DevOps, Communication
- Checkpoint and resume for long-running tasks
- Inter-agent communication via shared context

### Vision & Screen Intelligence

- Screen understanding and element detection
- Application detection and context awareness
- Dialog detection and interaction suggestions
- Workflow recording and replay
- Hand gesture control (local computer vision)

### Communication Hub

- **Email**: Read, send, search, importance intelligence
- **Messaging**: Unified message interface (SMS, browser)
- **Calls**: Call management with permission controls
- **Scheduled messages**: Queue for future delivery

### DevOps

- Container health monitoring
- Server status tracking
- Cloud deployment integration
- CI/CD file detection
- Environment diagnostics

### Personalization

- Explicit and inferred preference tracking
- Workflow detection and suggestions
- Skill suggestions based on usage patterns
- Personalization analytics dashboard

### Automatic Updates

JARVIS monitors the GitHub main branch for updates — no manual releases needed. Simply push a commit and enabled users receive the update:

```bash
git add .
git commit -m "..."
git push origin main
```

Configuration available in **Settings → Updates**.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Tauri Desktop (Rust)                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │           React / TypeScript Frontend                   │   │
│   │  ┌────┐┌────┐┌────┐┌────┐┌──────┐┌──────┐┌────────┐   │   │
│   │  │Chat││Voice││Visn││Code││Tools ││Skills││Memory  │   │   │
│   │  └────┘└────┘└────┘└────┘└──────┘└──────┘└────────┘   │   │
│   │  ┌────┐┌────┐┌──────┐┌────────┐┌──────┐┌──────────┐  │   │
│   │  │Research││Browser ││DevOps  ││Workflow││Settings │  │   │
│   │  └────┘└────┘└──────┘└────────┘└──────┘└──────────┘  │   │
│   └──────────────────────┬─────────────────────────────────┘   │
└──────────────────────────┼─────────────────────────────────────┘
                           │ WebSocket / REST
┌──────────────────────────┼─────────────────────────────────────┐
│              FastAPI Backend (Python)                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐  │
│  │ AI Providers│ │   Voice     │ │      Computer Control    │  │
│  │ - Groq      │ │ - Kokoro    │ │ - Screenshot / Screen   │  │
│  │ - Gemini    │ │ - espeak-ng │ │ - Mouse / Keyboard      │  │
│  │ - OpenRouter│ │ - Google STT│ │ - Applications           │  │
│  │ - Local LLM │ │ - Wake word │ │ - Terminal / Processes   │  │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐  │
│  │   Memory    │ │   Browser   │ │         Vision          │  │
│  │ - SQLite    │ │ - Playwright│ │ - Screen understanding  │  │
│  │ - ChromaDB  │ │ - Sessions  │ │ - Gestures (CV)         │  │
│  │ - Embeddings│ │ - Recovery  │ │ - Dialog detection      │  │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐  │
│  │   Coding    │ │   DevOps    │ │       Research          │  │
│  │ - Agent(s)  │ │ - Containers│ │ - Pipeline              │  │
│  │ - Git       │ │ - Deploy    │ │ - Sources               │  │
│  │ - Projects  │ │ - Monitor   │ │ - Claims                │  │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐  │
│  │  Skills     │ │ Automations │ │      Updater            │  │
│  │ - Registry  │ │ - Scheduler │ │ - GitHub commit check   │  │
│  │ - Router    │ │ - Scopes    │ │ - Atomic install        │  │
│  │ - Executor  │ │ - Retry     │ │ - Backup/rollback       │  │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Configuration

After installation:

```bash
cp .env.example .env
# Edit .env with your API keys and preferences
```

### AI Providers

| Provider | Env Vars | Notes |
|----------|----------|-------|
| Groq | `GROQ_API_KEY`, `GROQ_MODEL` | Default provider |
| Gemini | `GEMINI_API_KEY`, `GEMINI_MODEL` | Optional |
| OpenRouter | `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` | Optional |
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
| Wake Word Enabled | `WAKE_WORD_ENABLED` | `false` |

### Language

| Setting | Env Var | Default |
|---------|---------|---------|
| Language Mode | `LANGUAGE_MODE` | `auto` |

Auto-detects English, Urdu, Roman Urdu, and Hinglish.

### Optional Dependencies

| Feature | Install Command |
|---------|----------------|
| Kokoro TTS | `pip install kokoro` (Python 3.11/3.12) |
| ChromaDB | `pip install chromadb sentence-transformers` |
| Playwright | `npx playwright install --with-deps chromium` |
| PyAudio | `pip install pyaudio` (or `apt install portaudio19-dev`) |

---

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

# Build frontend
npm run build

# Build desktop app
npm run tauri:build
```

---

## Security

See [SECURITY.md](SECURITY.md) for API key handling, secrets management, and tool permission levels.

Key security features:

- **Permission System**: Per-action permissions with trust levels (trusted / ask / sensitive)
- **Confirmation Workflows**: Destructive actions require explicit approval
- **Emergency Stop**: Configurable hotkey to halt all automation
- **Scope Control**: Automations limited to specific scope categories
- **Data Isolation**: Memory databases never sent to external services
- **Local-First**: All data stored locally; no telemetry or tracking

---

## Automatic Updates

JARVIS monitors the `main` branch on GitHub for updates. A maintainer push automatically becomes an available update for users with automatic updates enabled. Configure in **Settings → Updates**.

See [updater/](updater/) for the updater service implementation.

---

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — System design and module layout
- [SECURITY.md](SECURITY.md) — Security policies and best practices
- [AUDIT_REPORT.md](AUDIT_REPORT.md) — System audit and issue tracking
- [FEATURE_MATRIX.md](FEATURE_MATRIX.md) — Feature implementation matrix

---

## Project Status

**Active Development** — Phase 31 complete. The system is functional and tested (773 tests passing). See [FEATURE_MATRIX.md](FEATURE_MATRIX.md) for the full feature implementation matrix and [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for known limitations.

| Component | Status |
|-----------|--------|
| Core assistant | Production-ready |
| AI providers | Production-ready |
| Voice (TTS/STT) | Production-ready (Kokoro + espeak-ng + Google STT) |
| Memory system | Production-ready |
| Skills system | Production-ready |
| Browser automation | Production-ready |
| Coding agent | Production-ready |
| DevOps | Production-ready |
| Research | Production-ready |
| Workflows | Production-ready |
| Computer control | Production-ready (Linux) |
| Vision | Production-ready |
| Gesture control | Functional |
| Communication | Functional (email, messaging) |
| Desktop app (Tauri) | Production-ready |
| Automatic updates | Production-ready |

### Known Platform Limitations

- **Computer control**: Full input control supported on Linux; Windows/macOS implementations are stubs (contributions welcome)
- **Updater**: Automatic installation not yet implemented (manual "Check Now" works)
- **Call control**: Integration framework exists; provider connection is stub

---

## Contributing

Contributions are welcome! Please read [SECURITY.md](SECURITY.md) first.

To contribute code:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python -m pytest tests/ -q`
5. Submit a pull request

---

## License

MIT License — see [LICENSE](LICENSE) for details.

Copyright &copy; 2025&ndash;2026 the JARVIS / ALYA contributors.