"""JARVIS application settings.

Loaded from `.env` via pydantic-settings. Settings changed through the API are
persisted back to `.env` so they survive restarts. Secrets stay on the backend
and are never returned unmasked to the browser.
"""

from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(".env")

# Non-secret keys that are safe to persist and display.
PUBLIC_SETTING_KEYS = {
    "assistant_name",
    "user_name",
    "language",
    "response_style",
    "persona",
    "groq_model",
    "groq_temperature",
    "groq_max_tokens",
    "groq_streaming",
    "context_length",
    "ai_provider",
    "gemini_model",
    "openrouter_model",
    "local_llm_url",
    "local_llm_model",
    "local_llm_enabled",
    "local_llm_api_type",
    "local_llm_timeout",
    "auto_failover",
    "provider_priority",
    "tts_engine",
    "tts_voice",
    "tts_speed",
    "tts_volume",
    "tts_enabled",
    "voice_enabled",
    "voice_language",
    "mic_device",
    "wake_word_enabled",
    "wake_word",
    "memory_enabled",
    "vector_memory_enabled",
    "auto_memory_enabled",
    "project_memory_enabled",
    "conversation_summaries_enabled",
    "memory_retrieval_enabled",
    "cloud_memory_sharing",
    "memory_retention_short_term_hours",
    "memory_retention_task_history_days",
    "memory_retention_summaries_days",
    "proactive_mode",
    "proactive_min_interval_minutes",
    "message_notifications_enabled",
    "browser_notifications_enabled",
    "voice_notifications_enabled",
    "desktop_notifications_enabled",
    "theme",
    "accent_color",
    "glow_intensity",
    "animation_level",
    "orb_size",
    "compact_ui",
    "panel_transparency",
    "background_particles",
    "reduced_motion",
    "font_size",
    "ui_preset",
    "log_level",
    "vision_enabled",
    "vision_provider",
    "vision_confidence_threshold",
    "vision_local_model",
    "vision_cloud_model",
    "vision_max_retries",
    "vision_cache_ttl",
    "vision_capture_hotkey",
    "research_max_sources",
    "research_depth",
    "research_document_format",
}

# Secret keys stored in `.env` but never returned unmasked to the browser.
SECRET_SETTING_KEYS = {
    "groq_api_key",
    "local_llm_api_key",
    "gemini_api_key",
    "openrouter_api_key",
    "web_search_api_key",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    # General
    assistant_name: str = "JARVIS"
    user_name: str = "Sir"
    language: str = "en"
    response_style: str = "balanced"
    persona: str = "jarvis"

    # Groq
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_temperature: float = 0.7
    groq_max_tokens: int = 1024
    groq_streaming: bool = True
    context_length: int = 10000

    # Provider selection: auto | groq | local | gemini | openrouter
    ai_provider: str = "auto"
    auto_failover: bool = True
    provider_priority: str = "groq_first"

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # OpenRouter
    openrouter_api_key: str = ""
    openrouter_model: str = "google/gemini-2.0-flash-001"

    # Local LLM
    local_llm_url: str = ""
    local_llm_model: str = ""
    local_llm_enabled: bool = False
    local_llm_api_key: str = ""
    local_llm_api_type: str = "openai"
    local_llm_timeout: int = 60

    # Voice / TTS
    voice_enabled: bool = True
    voice_language: str = "en-US"
    mic_device: str = ""
    wake_word_enabled: bool = False
    wake_word: str = "Hey JARVIS"
    stt_engine: str = "google"
    vosk_model_path: str = ""
    tts_engine: str = "espeak-ng"
    tts_voice: str = "en+f3"
    tts_speed: int = 160
    tts_volume: int = 80
    tts_enabled: bool = True
    tts_venv_dir: str = ""
    tts_cache_dir: str = ""
    kokoro_model_path: str = ""

    # Memory
    memory_enabled: bool = True
    vector_memory_enabled: bool = False
    auto_memory_enabled: bool = False
    project_memory_enabled: bool = True
    conversation_summaries_enabled: bool = True
    memory_retrieval_enabled: bool = True
    cloud_memory_sharing: str = "ask"
    memory_retention_short_term_hours: int = 24
    memory_retention_task_history_days: int = 30
    memory_retention_summaries_days: int = 30
    proactive_mode: bool = False
    proactive_min_interval_minutes: int = 10

    # Notifications
    message_notifications_enabled: bool = True
    browser_notifications_enabled: bool = True
    voice_notifications_enabled: bool = True
    desktop_notifications_enabled: bool = True

    # Appearance
    theme: str = "dark"
    accent_color: str = "cyan"
    glow_intensity: int = 50
    animation_level: str = "full"
    orb_size: int = 64
    compact_ui: bool = False
    panel_transparency: int = 85
    background_particles: bool = True
    reduced_motion: bool = False
    font_size: str = "normal"
    ui_preset: str = "jarvis"

    # System
    debug: bool = False
    log_level: str = "INFO"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:5173"
    data_dir: str = "data"
    db_path: str = "data/jarvis.db"
    logs_dir: str = "logs"
    auto_start_frontend: bool = True

    # Web search
    web_search_api_key: str = ""

    # Language
    language_mode: str = "auto"

    # Vision
    vision_enabled: bool = False
    vision_provider: str = ""
    vision_confidence_threshold: float = 0.70
    vision_local_model: str = ""
    vision_cloud_model: str = ""
    vision_max_retries: int = 3
    vision_cache_ttl: float = 30.0
    vision_capture_hotkey: str = "ctrl+shift+j"

    # Deep Research
    research_max_sources: int = 20
    research_depth: str = "deep"
    research_document_format: str = "markdown"

    # ---- persistence -------------------------------------------------
    def apply_db_overrides(self, overrides: dict[str, str]) -> None:
        """Apply string values (from the settings DB table) on top of env."""
        for key, value in overrides.items():
            if not hasattr(self, key):
                continue
            current = getattr(self, key)
            try:
                if isinstance(current, bool):
                    setattr(self, key, str(value).lower() in ("true", "1", "yes", "on"))
                elif isinstance(current, int):
                    setattr(self, key, int(value))
                elif isinstance(current, float):
                    setattr(self, key, float(value))
                else:
                    setattr(self, key, value)
            except (ValueError, TypeError):
                pass

    def to_env(self) -> dict[str, str]:
        """Serialize non-secret settings to `.env` key/value pairs."""
        out: dict[str, str] = {}
        for key in sorted(PUBLIC_SETTING_KEYS | SECRET_SETTING_KEYS):
            if not hasattr(self, key):
                continue
            value = getattr(self, key)
            if isinstance(value, bool):
                out[key] = "true" if value else "false"
            elif isinstance(value, (int, float)):
                out[key] = str(value)
            else:
                out[key] = str(value)
        return out

    def persist(self) -> None:
        """Write settings to `.env` and lock down its permissions."""
        existing: dict[str, str] = {}
        if ENV_FILE.exists():
            for line in ENV_FILE.read_text().splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    key, _, value = line.partition("=")
                    existing[key.strip()] = value.strip()
        for key, value in self.to_env().items():
            existing[key] = value
        lines = [f"{key}={value}" for key, value in sorted(existing.items())]
        ENV_FILE.write_text("\n".join(lines) + "\n")
        try:
            os.chmod(ENV_FILE, 0o600)
        except OSError:
            pass


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> Settings:
    """Reload settings from disk (used by the reset endpoint)."""
    global _settings
    _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Create a fresh Settings instance while keeping the singleton semantics."""
    global _settings
    _settings = Settings()
    return _settings
