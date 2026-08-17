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
    "memory_ranking_enabled",
    "memory_decay_enabled",
    "memory_decay_rate",
    "memory_duplicate_detection",
    "memory_contradiction_detection",
    "memory_auto_extraction",
    "memory_temporary_chat",
    "memory_max_context_memories",
    "memory_max_context_tokens",
    "memory_ask_before_remember",
    "memory_session_memory_enabled",
    "memory_private_mode",
    "memory_audit_log_enabled",
    "memory_prompt_injection_protection",
    "memory_hybrid_search_enabled",
    "memory_semantic_search_enabled",
    "memory_keyword_fallback_enabled",
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
    "vision_max_image_size_mb",
    "vision_max_image_width",
    "vision_max_image_height",
    "vision_image_quality",
    "vision_ocr_enabled",
    "vision_camera_enabled",
    "vision_screen_analysis_enabled",
    "vision_remember_visual_context",
    "vision_external_provider_allowed",
    "vision_screen_access",
    "vision_continuous_vision",
    "vision_camera_access",
    "vision_visual_overlay",
    "vision_screen_history_minutes",
    "vision_max_visual_steps",
    "vision_ocr_preprocessing",
    "vision_offline_fallback",
    "vision_prompt_injection_protection",
    "research_max_sources",
    "research_depth",
    "research_document_format",
    "agent_enabled",
    "agent_auto_execute",
    "agent_auto_fix",
    "agent_max_retries",
    "agent_confirmation_level",
    "agent_terminal",
    "agent_filesystem_delete",
    "agent_network",
    "agent_git",
    "agent_autonomy_level",
    "agent_dry_run",
    "agent_background_tasks_enabled",
    "agent_require_confirmation_communicate",
    "agent_require_confirmation_delete",
    "agent_require_confirmation_system",
    "agent_require_confirmation_purchases",
    "agent_require_confirmation_publishing",
    "agent_kill_switch_enabled",
    "agent_max_task_time",
    "agent_max_steps",
    "agent_max_parallel_tasks",
    "agent_file_conflict_protection",
    "agent_orchestration_enabled",
    "agent_multi_agent_mode",
    "agent_max_active_agents",
    "agent_max_task_steps",
    "agent_task_timeout",
    "agent_agent_timeout",
    "agent_cost_limit",
    "agent_logging_enabled",
    "agent_custom_agents_enabled",
    "task_autonomy_level",
    "task_dry_run",
    "task_max_concurrent",
    "task_default_timeout",
    "task_default_retries",
    "task_command_security",
    "task_process_tracking",
    "browser_enabled",
    "browser_engine",
    "browser_mode",
    "browser_profile",
    "browser_download_dir",
    "browser_search_engine",
    "browser_permission",
    "browser_timeout",
    "browser_max_retries",
    "browser_trusted_domains",
    "browser_visual_fallback",
    "browser_ask_before_send",
    "browser_ask_before_post",
    "browser_ask_before_upload",
    "browser_ask_before_download",
    "browser_ask_before_purchase",
    "browser_auto_captcha_pause",
    "browser_max_actions",
    "browser_max_page_reloads",
    "browser_dom_first",
    "computer_enabled",
    "computer_mode",
    "computer_screen_access",
    "computer_mouse_control",
    "computer_keyboard_control",
    "computer_application_launch",
    "computer_window_control",
    "computer_screen_preview",
    "computer_mouse_failsafe",
    "computer_max_retries",
    "computer_file_automation",
    "computer_terminal_automation",
    "computer_process_control",
    "computer_trust_level",
    "computer_emergency_stop",
    "computer_automation_timeout",
    "computer_max_task_steps",
    "computer_visual_confidence",
    "computer_window_layouts",
    "computer_clipboard_access",
    "workflow_max_concurrent",
    "workflow_default_timeout",
    "workflow_default_retries",
    "workflow_quiet_hours_start",
    "workflow_quiet_hours_end",
    "workflow_history_retention_days",
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
    memory_ranking_enabled: bool = True
    memory_decay_enabled: bool = True
    memory_decay_rate: float = 0.01
    memory_duplicate_detection: bool = True
    memory_contradiction_detection: bool = True
    memory_auto_extraction: bool = False
    memory_temporary_chat: bool = False
    memory_max_context_memories: int = 8
    memory_max_context_tokens: int = 2000
    memory_ask_before_remember: bool = False
    memory_session_memory_enabled: bool = True
    memory_private_mode: bool = False
    memory_audit_log_enabled: bool = True
    memory_prompt_injection_protection: bool = True
    memory_hybrid_search_enabled: bool = True
    memory_semantic_search_enabled: bool = True
    memory_keyword_fallback_enabled: bool = True

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
    vision_max_image_size_mb: float = 20.0
    vision_max_image_width: int = 1920
    vision_max_image_height: int = 1080
    vision_image_quality: int = 85
    vision_ocr_enabled: bool = True
    vision_camera_enabled: bool = False
    vision_screen_analysis_enabled: bool = True
    vision_remember_visual_context: bool = False
    vision_external_provider_allowed: bool = True
    vision_screen_access: bool = False
    vision_continuous_vision: bool = False
    vision_camera_access: bool = False
    vision_visual_overlay: bool = False
    vision_screen_history_minutes: int = 0
    vision_max_visual_steps: int = 10
    vision_ocr_preprocessing: bool = True
    vision_offline_fallback: bool = True
    vision_prompt_injection_protection: bool = True

    # Deep Research
    research_max_sources: int = 20
    research_depth: str = "deep"
    research_document_format: str = "markdown"

    # Agent
    agent_enabled: bool = True
    agent_auto_execute: bool = False
    agent_auto_fix: bool = True
    agent_max_retries: int = 3
    agent_confirmation_level: str = "risky_only"
    agent_terminal: str = "ask"
    agent_filesystem_delete: str = "ask"
    agent_network: str = "ask"
    agent_git: str = "ask"
    agent_autonomy_level: str = "assisted"
    agent_dry_run: bool = False
    agent_background_tasks_enabled: bool = True
    agent_require_confirmation_communicate: bool = True
    agent_require_confirmation_delete: bool = True
    agent_require_confirmation_system: bool = True
    agent_require_confirmation_purchases: bool = True
    agent_require_confirmation_publishing: bool = True
    agent_kill_switch_enabled: bool = True
    agent_max_task_time: int = 1800
    agent_max_steps: int = 50
    agent_max_parallel_tasks: int = 2
    agent_file_conflict_protection: bool = True
    agent_orchestration_enabled: bool = True
    agent_multi_agent_mode: str = "auto"
    agent_max_active_agents: int = 5
    agent_max_parallel_tasks: int = 3
    agent_max_task_steps: int = 20
    agent_task_timeout: int = 600
    agent_agent_timeout: int = 300
    agent_cost_limit: str = "off"
    agent_logging_enabled: bool = False
    agent_custom_agents_enabled: bool = True

    # Task Engine
    task_autonomy_level: str = "balanced"
    task_dry_run: bool = False
    task_max_concurrent: int = 3
    task_default_timeout: int = 600
    task_default_retries: int = 3
    task_command_security: bool = True
    task_process_tracking: bool = True

    # Browser
    browser_enabled: bool = True
    browser_engine: str = "chromium"
    browser_mode: str = "visible"
    browser_profile: str = "isolated"
    browser_download_dir: str = "~/Downloads/JARVIS-Browser"
    browser_search_engine: str = "https://www.google.com"
    browser_permission: str = "ask"
    browser_timeout: int = 30
    browser_max_retries: int = 3
    browser_trusted_domains: list[str] = ["github.com", "docs.python.org", "developer.mozilla.org"]
    browser_visual_fallback: bool = True
    browser_ask_before_send: bool = True
    browser_ask_before_post: bool = True
    browser_ask_before_upload: bool = True
    browser_ask_before_download: bool = False
    browser_ask_before_purchase: bool = True
    browser_auto_captcha_pause: bool = True
    browser_max_actions: int = 10
    browser_max_page_reloads: int = 3
    browser_dom_first: bool = True

    # Computer
    computer_enabled: bool = True
    computer_mode: str = "off"
    computer_screen_access: str = "ask"
    computer_mouse_control: str = "ask"
    computer_keyboard_control: str = "ask"
    computer_application_launch: str = "ask"
    computer_window_control: str = "ask"
    computer_screen_preview: str = "off"
    computer_mouse_failsafe: bool = True
    computer_max_retries: int = 3
    computer_file_automation: str = "ask"
    computer_terminal_automation: str = "ask"
    computer_process_control: str = "ask"
    computer_trust_level: str = "ask_sensitive"
    computer_emergency_stop: str = "ctrl+alt+shift+j"
    computer_automation_timeout: int = 30
    computer_max_task_steps: int = 20
    computer_visual_confidence: float = 0.70
    computer_window_layouts: bool = True
    computer_clipboard_access: str = "ask"
    workflow_max_concurrent: int = 3
    workflow_default_timeout: int = 600
    workflow_default_retries: int = 2
    workflow_quiet_hours_start: str = "23:00"
    workflow_quiet_hours_end: str = "08:00"
    workflow_history_retention_days: int = 30

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
