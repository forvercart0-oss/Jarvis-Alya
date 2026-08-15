# Security

## Secrets Management

- **Never** commit `.env` to version control.
- API keys are stored exclusively in `.env` (file permission `0o600`).
- The React frontend receives **masked** API keys only (`gsk_****079J`).
- Secrets are never written to `localStorage`, `sessionStorage`, or cookies.
- Settings endpoints redact keys before returning them to the browser.

## Network Security

- CORS is restricted to localhost and Tauri protocol origins.
- All third-party API calls (Groq, Gemini, OpenRouter) are made server-side.
- The backend never forwards raw user credentials to external services.

## Tool Safety

- Dangerous commands (`rm -rf`, `mkfs`, `dd`, `shutdown`, etc.) require explicit confirmation.
- Protected directories (`/etc`, `/bin`, `/usr/bin`, `/sbin`, `/sys`, `/proc`, `/dev`) are blocked by default.
- Tool execution results are validated before being passed to the AI.

## Voice Privacy

- Voice input is processed locally or via configured STT provider.
- Wake word detection runs locally.
- Audio buffers are not persisted to disk.

## Data Retention

- Conversations are stored in `data/jarvis.db` (SQLite).
- Vector memory (ChromaDB) is optional and stored in `data/vector_store`.
- Users can clear memory via Settings or API.
- No telemetry is sent to third parties.

## Update Integrity

- Updates are fetched only from the configured GitHub repository.
- Release artifacts are verified when possible.
- User data (`.env`, `data/`, `logs/`) is never overwritten by updates.

## Reporting Vulnerabilities

Report security issues privately. Do not open public issues for security vulnerabilities.
