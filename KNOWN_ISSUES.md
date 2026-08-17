# JARVIS 2.0 — Known Issues

## P0 — Critical

None currently identified. All 750 tests pass.

## P1 — High

| Issue | Description | Workaround |
|-------|-------------|------------|
| Windows/macOS computer control | Platform providers are stubs; mouse/keyboard/window management not functional on Windows/macOS | Use Linux for full computer control |
| Vision model provider | No local vision LLM integrated; OCR uses tesseract CLI only | Install tesseract-ocr |
| Updater system | No automatic update mechanism exists | Manual update via git pull + reinstall |
| Wayland screen capture | Requires grim or gnome-screenshot; may not work on all Wayland compositors | Install grim |

## P2 — Medium

| Issue | Description | Workaround |
|-------|-------------|------------|
| Frontend chunk size | Main JS bundle is ~1MB gzipped to ~278KB | Acceptable for desktop app |
| TypeScript strictness | `noUnusedLocals`/`noUnusedParameters` enabled; some props prefixed with `_` | No functional impact |
| STT engine | Google STT requires internet; Vosk needs manual model download | Use internet or install Vosk model |
| Kokoro TTS | Requires separate Python 3.11/3.12 venv (tts-venv) | Run install.sh |
| Memory panel props | Some Phase 29 props unused in current UI tabs | Will be used in future UI updates |

## P3 — Low

| Issue | Description |
|-------|-------------|
| CommunicationPanel | Some endpoints may return empty data if providers not configured |
| DevOpsPanel | Rollback and supply-chain scan buttons show "not available" |
| Orb states | Some states map to same orb animation |
| Log rotation | Not implemented; logs can grow indefinitely |
| Accessibility | Keyboard navigation and ARIA labels incomplete |

## Deferred

| Feature | Reason |
|---------|--------|
| Automatic updater | Requires GitHub release pipeline |
| Windows UI Automation | Requires Windows-specific Rust/Python bindings |
| macOS Accessibility | Requires macOS-specific bindings |
| Camera-based gestures | Requires MediaPipe + privacy infrastructure |
| Production code signing | Requires CI/CD + certificates |
