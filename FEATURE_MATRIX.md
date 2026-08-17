# JARVIS 2.0 — Feature Matrix

| Feature | Implemented | Tested | Working | Platform | Notes |
|---------|-------------|--------|---------|----------|-------|
| Desktop App (Tauri) | ✅ | ✅ | ✅ | Linux/Windows/macOS | Rust backend, frameless window |
| AI Router | ✅ | ✅ | ✅ | All | Groq, Gemini, OpenRouter, Local LLM |
| Groq Integration | ✅ | ✅ | ✅ | All | Default provider, streaming |
| Gemini Integration | ✅ | ✅ | ✅ | All | Fallback provider |
| OpenRouter Integration | ✅ | ✅ | ✅ | All | Fallback provider |
| Local LLM | ✅ | ✅ | ✅ | All | Ollama/OpenAI-compatible |
| Kokoro TTS | ✅ | ✅ | ✅ | All | Low-latency streaming, queue |
| STT (Google/Vosk) | ✅ | ✅ | ✅ | All | Wake word support |
| Profile Switching | ✅ | ✅ | ✅ | All | JARVIS/ALYA at runtime |
| Memory (SQLite) | ✅ | ✅ | ✅ | All | Conversations, preferences |
| Vector Memory | ✅ | ✅ | ✅ | All | ChromaDB optional |
| Phase 29 Memory | ✅ | ✅ | ✅ | All | Ideas, error memory, pinning |
| Skills System | ✅ | ✅ | ✅ | All | JSON-based, import/export |
| Coding Agent | ✅ | ✅ | ✅ | All | Project inspection, editing |
| DevOps Agent | ✅ | ✅ | ✅ | All | Deploy, containers, servers |
| Browser Intelligence | ✅ | ✅ | ✅ | All | Playwright, DOM automation |
| Computer Control | ✅ | ✅ | ✅ | Linux | xdotool/ydotool/wtype |
| Screen Capture | ✅ | ✅ | ✅ | Linux | grim, gnome-screenshot |
| OCR | ✅ | ✅ | ✅ | All | Tesseract CLI |
| UI Detection | ✅ | ✅ | ✅ | All | Pattern + vision-based |
| Visual Targeting | ✅ | ✅ | ✅ | All | Confidence-based |
| Action Planner | ✅ | ✅ | ✅ | All | Natural language commands |
| Action Verification | ✅ | ✅ | ✅ | All | Screen diff after actions |
| Screen Diff | ✅ | ✅ | ✅ | All | Change detection |
| Screen Understanding | ✅ | ✅ | ✅ | All | App-aware context |
| Application Understanding | ✅ | ✅ | ✅ | All | Firefox, Chrome, VS Code, etc. |
| Dialog Detection | ✅ | ✅ | ✅ | All | Confirmation, error, warning, CAPTCHA |
| Workflow Recorder | ✅ | ✅ | ✅ | All | Record/replay visual actions |
| Visual Skills | ✅ | ✅ | ✅ | All | App-specific automation |
| Gesture Architecture | ✅ | ✅ | ✅ | All | Future-ready, disabled by default |
| Browser Automation | ✅ | ✅ | ✅ | All | DOM + accessibility priority |
| Terminal Understanding | ✅ | ✅ | ✅ | All | Error detection, output reading |
| Editor Understanding | ✅ | ✅ | ✅ | All | VS Code, Neovim recognition |
| File Manager Understanding | ✅ | ✅ | ✅ | All | Dolphin, navigation |
| Deep Research | ✅ | ✅ | ✅ | All | Multi-source, document generation |
| Serious Mode | ✅ | ✅ | ✅ | All | Red theme, research focus |
| Full Auto | ✅ | ✅ | ✅ | All | Policy-guarded automation |
| Task Graph | ✅ | ✅ | ✅ | All | Plan → execute → verify → recover |
| Recovery Engine | ✅ | ✅ | ✅ | All | Auto-retry, safe fallback |
| Verification Engine | ✅ | ✅ | ✅ | All | Post-action verification |
| Policy Engine | ✅ | ✅ | ✅ | All | Safety boundaries |
| WebSocket | ✅ | ✅ | ✅ | All | Reconnect, heartbeat, events |
| Notifications | ✅ | ✅ | ✅ | All | Task, message, error alerts |
| Settings | ✅ | ✅ | ✅ | All | Persistent, categorized |
| Theme Engine | ✅ | ✅ | ✅ | All | JARVIS/ALYA themes |
| Reduced Motion | ✅ | ✅ | ✅ | All | Accessibility |
| Voice + Vision | ✅ | ✅ | ✅ | All | "What's on my screen?" |
| Computer Vision | ✅ | ✅ | ✅ | All | Screen understanding |
| Multi-monitor | ✅ | ✅ | ✅ | Linux | Primary/secondary/all |
| Active Window Detection | ✅ | ✅ | ✅ | Linux | App, title, position |
| Linux Support | ✅ | ✅ | ✅ | Linux | Wayland + X11 |
| Windows Support | ⚠️ | ⚠️ | ⚠️ | Windows | Partial, needs providers |
| macOS Support | ⚠️ | ⚠️ | ⚠️ | macOS | Partial, needs providers |
| Installer (Linux) | ✅ | ✅ | ✅ | Linux | Idempotent, Arch/Debian/Fedora |
| Installer (Windows) | ✅ | ✅ | ✅ | Windows | PowerShell, winget/choco |
| Installer (macOS) | ✅ | ✅ | ✅ | macOS | Homebrew-based |
| Run Scripts | ✅ | ✅ | ✅ | All | Linux/macOS/Windows |
| Updater | ❌ | ❌ | ❌ | All | Not implemented |
| Loading Screen | ✅ | ✅ | ✅ | All | Startup sequence |
| Offline Mode | ✅ | ✅ | ✅ | All | Local services fallback |
| E2E Test | ⚠️ | ⚠️ | ⚠️ | All | Manual verification needed |
