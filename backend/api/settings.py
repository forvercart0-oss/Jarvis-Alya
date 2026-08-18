from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from config.settings import get_settings

router = APIRouter()


class SettingsUpdate(BaseModel):
    assistant_name: Optional[str] = None
    user_name: Optional[str] = None
    voice_enabled: Optional[bool] = None
    voice_language: Optional[str] = None
    tts_enabled: Optional[bool] = None
    tts_voice: Optional[str] = None
    tts_speed: Optional[int] = None
    tts_volume: Optional[int] = None
    wake_word_enabled: Optional[bool] = None
    wake_word: Optional[str] = None
    memory_enabled: Optional[bool] = None
    vector_memory_enabled: Optional[bool] = None
    message_notifications_enabled: Optional[bool] = None
    browser_notifications_enabled: Optional[bool] = None
    voice_notifications_enabled: Optional[bool] = None
    desktop_notifications_enabled: Optional[bool] = None
    debug: Optional[bool] = None
    groq_model: Optional[str] = None
    groq_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    openrouter_model: Optional[str] = None
    local_llm_url: Optional[str] = None
    local_llm_model: Optional[str] = None
    local_llm_enabled: Optional[bool] = None
    local_llm_api_key: Optional[str] = None
    local_llm_api_type: Optional[str] = None
    local_llm_timeout: Optional[int] = None
    tts_engine: Optional[str] = None
    tts_venv_dir: Optional[str] = None
    tts_cache_dir: Optional[str] = None
    kokoro_model_path: Optional[str] = None
    response_style: Optional[str] = None
    language: Optional[str] = None
    auto_failover: Optional[bool] = None
    provider_priority: Optional[str] = None
    theme: Optional[str] = None
    accent_color: Optional[str] = None
    glow_intensity: Optional[int] = None
    animation_level: Optional[str] = None
    orb_size: Optional[int] = None
    persona: Optional[str] = None
    compact_ui: Optional[bool] = None
    panel_transparency: Optional[int] = None
    background_particles: Optional[bool] = None
    reduced_motion: Optional[bool] = None
    font_size: Optional[str] = None
    language_mode: Optional[str] = None
    image_generation_enabled: Optional[bool] = None
    image_provider: Optional[str] = None
    pixazo_api_key: Optional[str] = None
    puter_api_key: Optional[str] = None
    video_generation_enabled: Optional[bool] = None
    video_provider: Optional[str] = None
    fal_api_key: Optional[str] = None
    magic_hour_api_key: Optional[str] = None
    gesture_control_enabled: Optional[bool] = None
    gesture_camera_device: Optional[str] = None
    gesture_sensitivity: Optional[int] = None
    call_control_enabled: Optional[bool] = None
    call_provider: Optional[str] = None
    call_api_key: Optional[str] = None
    call_assist_mode: Optional[str] = None
    vision_enabled: Optional[bool] = None
    vision_provider: Optional[str] = None
    vision_confidence_threshold: Optional[float] = None
    vision_local_model: Optional[str] = None
    vision_cloud_model: Optional[str] = None
    vision_max_retries: Optional[int] = None
    vision_cache_ttl: Optional[float] = None
    vision_capture_hotkey: Optional[str] = None
    research_max_sources: Optional[int] = None
    research_depth: Optional[str] = None
    research_document_format: Optional[str] = None
    agent_enabled: Optional[bool] = None
    agent_auto_execute: Optional[bool] = None
    agent_auto_fix: Optional[bool] = None
    agent_max_retries: Optional[int] = None
    agent_confirmation_level: Optional[str] = None
    agent_terminal: Optional[str] = None
    agent_filesystem_delete: Optional[str] = None
    agent_network: Optional[str] = None
    agent_git: Optional[str] = None
    browser_enabled: Optional[bool] = None
    browser_engine: Optional[str] = None
    browser_mode: Optional[str] = None
    browser_profile: Optional[str] = None
    browser_download_dir: Optional[str] = None
    browser_search_engine: Optional[str] = None
    browser_permission: Optional[str] = None
    browser_timeout: Optional[int] = None
    browser_max_retries: Optional[int] = None
    computer_enabled: Optional[bool] = None
    computer_mode: Optional[str] = None
    computer_screen_access: Optional[str] = None
    computer_mouse_control: Optional[str] = None
    computer_keyboard_control: Optional[str] = None
    computer_application_launch: Optional[str] = None
    computer_window_control: Optional[str] = None
    computer_screen_preview: Optional[str] = None
    computer_mouse_failsafe: Optional[bool] = None
    computer_max_retries: Optional[int] = None


def _mask_api_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return key[:2] + "****"
    return key[:4] + "****" + key[-4:]


@router.get("/settings")
async def get_settings_api():
    s = get_settings()
    from backend.main import memory_manager
    db_settings = memory_manager.store.get_all_settings()
    return {
        "assistant_name": s.assistant_name,
        "user_name": s.user_name,
        "voice_enabled": s.voice_enabled,
        "voice_language": s.voice_language,
        "tts_enabled": s.tts_enabled,
        "tts_voice": s.tts_voice,
        "tts_speed": s.tts_speed,
        "tts_volume": s.tts_volume,
        "wake_word_enabled": s.wake_word_enabled,
        "wake_word": s.wake_word,
        "memory_enabled": s.memory_enabled,
        "vector_memory_enabled": s.vector_memory_enabled,
        "message_notifications_enabled": s.message_notifications_enabled,
        "browser_notifications_enabled": s.browser_notifications_enabled,
        "voice_notifications_enabled": s.voice_notifications_enabled,
        "desktop_notifications_enabled": s.desktop_notifications_enabled,
        "debug": s.debug,
        "groq_model": s.groq_model,
        "groq_api_key": _mask_api_key(s.groq_api_key),
        "gemini_api_key": _mask_api_key(s.gemini_api_key),
        "gemini_model": s.gemini_model,
        "openrouter_api_key": _mask_api_key(s.openrouter_api_key),
        "openrouter_model": s.openrouter_model,
        "local_llm_url": s.local_llm_url,
        "local_llm_model": s.local_llm_model,
        "local_llm_enabled": s.local_llm_enabled,
        "local_llm_api_key": _mask_api_key(s.local_llm_api_key),
        "local_llm_api_type": s.local_llm_api_type,
        "local_llm_timeout": s.local_llm_timeout,
        "tts_engine": s.tts_engine,
        "tts_venv_dir": getattr(s, "tts_venv_dir", ""),
        "tts_cache_dir": getattr(s, "tts_cache_dir", ""),
        "kokoro_model_path": getattr(s, "kokoro_model_path", ""),
        "response_style": s.response_style,
        "language": s.language,
        "auto_failover": s.auto_failover,
        "provider_priority": s.provider_priority,
        "theme": s.theme,
        "accent_color": s.accent_color,
        "glow_intensity": s.glow_intensity,
        "animation_level": s.animation_level,
        "orb_size": s.orb_size,
        "persona": s.persona,
        "compact_ui": getattr(s, "compact_ui", False),
        "panel_transparency": getattr(s, "panel_transparency", 85),
        "background_particles": getattr(s, "background_particles", True),
        "reduced_motion": getattr(s, "reduced_motion", False),
        "font_size": getattr(s, "font_size", "normal"),
        "language_mode": getattr(s, "language_mode", "auto"),
        "image_generation_enabled": getattr(s, "image_generation_enabled", True),
        "image_provider": getattr(s, "image_provider", "auto"),
        "pixazo_api_key": _mask_api_key(getattr(s, "pixazo_api_key", "")),
        "puter_api_key": _mask_api_key(getattr(s, "puter_api_key", "")),
        "video_generation_enabled": getattr(s, "video_generation_enabled", True),
        "video_provider": getattr(s, "video_provider", "auto"),
        "fal_api_key": _mask_api_key(getattr(s, "fal_api_key", "")),
        "magic_hour_api_key": _mask_api_key(getattr(s, "magic_hour_api_key", "")),
        "gesture_control_enabled": getattr(s, "gesture_control_enabled", False),
        "gesture_camera_device": getattr(s, "gesture_camera_device", ""),
        "gesture_sensitivity": getattr(s, "gesture_sensitivity", 50),
        "call_control_enabled": getattr(s, "call_control_enabled", False),
        "call_provider": getattr(s, "call_provider", ""),
        "call_assist_mode": getattr(s, "call_assist_mode", "notify_only"),
        "vision_enabled": getattr(s, "vision_enabled", False),
        "vision_provider": getattr(s, "vision_provider", ""),
        "vision_confidence_threshold": getattr(s, "vision_confidence_threshold", 0.70),
        "vision_local_model": getattr(s, "vision_local_model", ""),
        "vision_cloud_model": getattr(s, "vision_cloud_model", ""),
        "vision_max_retries": getattr(s, "vision_max_retries", 3),
        "vision_cache_ttl": getattr(s, "vision_cache_ttl", 30.0),
        "vision_capture_hotkey": getattr(s, "vision_capture_hotkey", "ctrl+shift+j"),
        "research_max_sources": getattr(s, "research_max_sources", 20),
        "research_depth": getattr(s, "research_depth", "deep"),
        "research_document_format": getattr(s, "research_document_format", "markdown"),
        "agent_enabled": getattr(s, "agent_enabled", True),
        "agent_auto_execute": getattr(s, "agent_auto_execute", False),
        "agent_auto_fix": getattr(s, "agent_auto_fix", True),
        "agent_max_retries": getattr(s, "agent_max_retries", 3),
        "agent_confirmation_level": getattr(s, "agent_confirmation_level", "risky_only"),
        "agent_terminal": getattr(s, "agent_terminal", "ask"),
        "agent_filesystem_delete": getattr(s, "agent_filesystem_delete", "ask"),
        "agent_network": getattr(s, "agent_network", "ask"),
        "agent_git": getattr(s, "agent_git", "ask"),
        "browser_enabled": getattr(s, "browser_enabled", True),
        "browser_engine": getattr(s, "browser_engine", "chromium"),
        "browser_mode": getattr(s, "browser_mode", "visible"),
        "browser_profile": getattr(s, "browser_profile", "isolated"),
        "browser_download_dir": getattr(s, "browser_download_dir", "~/Downloads/JARVIS-Browser"),
        "browser_search_engine": getattr(s, "browser_search_engine", "https://www.google.com"),
        "browser_permission": getattr(s, "browser_permission", "ask"),
        "browser_timeout": getattr(s, "browser_timeout", 30),
        "browser_max_retries": getattr(s, "browser_max_retries", 3),
        "browser_trusted_domains": getattr(s, "browser_trusted_domains", ["github.com", "docs.python.org", "developer.mozilla.org"]),
        "computer_enabled": getattr(s, "computer_enabled", True),
        "computer_mode": getattr(s, "computer_mode", "off"),
        "computer_screen_access": getattr(s, "computer_screen_access", "ask"),
        "computer_mouse_control": getattr(s, "computer_mouse_control", "ask"),
        "computer_keyboard_control": getattr(s, "computer_keyboard_control", "ask"),
        "computer_application_launch": getattr(s, "computer_application_launch", "ask"),
        "computer_window_control": getattr(s, "computer_window_control", "ask"),
        "computer_screen_preview": getattr(s, "computer_screen_preview", "off"),
        "computer_mouse_failsafe": getattr(s, "computer_mouse_failsafe", True),
        "computer_max_retries": getattr(s, "computer_max_retries", 3),
        "db_settings": db_settings,
    }


_TTS_FIELDS = {"tts_engine", "tts_voice", "tts_speed", "tts_volume", "tts_enabled", "tts_venv_dir", "tts_cache_dir", "kokoro_model_path"}
_PROVIDER_FIELDS = {"groq_api_key", "groq_model", "gemini_api_key", "gemini_model",
                    "openrouter_api_key", "openrouter_model", "local_llm_url", "local_llm_model",
                    "local_llm_enabled", "local_llm_api_key", "local_llm_api_type",
                    "local_llm_timeout", "provider_priority", "auto_failover"}


@router.put("/settings")
async def update_settings(update: SettingsUpdate):
    from backend.main import memory_manager, ai_service, tts_manager, vision_manager, ws_manager
    from backend.services.persona_service import persona_service
    s = get_settings()
    updates = update.model_dump(exclude_none=True)

    if "persona" in updates and str(updates["persona"]).lower() != s.persona:
        payload = await persona_service.switch(updates["persona"])
        updates.pop("persona")
        if payload.get("accent_color"):
            s.accent_color = payload["accent_color"]
        updates.pop("accent_color", None)

    for key, value in updates.items():
        if hasattr(s, key):
            setattr(s, key, value)
            if "api_key" in key and value:
                memory_manager.store.set_setting(key, value)
            else:
                memory_manager.store.set_setting(key, str(value))
    s.persist()
    if "vision_enabled" in updates:
        vision_manager.enabled = bool(updates["vision_enabled"])
        if vision_manager.enabled:
            await ws_manager.broadcast("vision_started", {"provider": vision_manager.status().get("provider")})
        else:
            await ws_manager.broadcast("vision_ready", {})
    if updates.keys() & _PROVIDER_FIELDS:
        ai_service.reconfigure_providers()
    if updates.keys() & _TTS_FIELDS:
        tts_manager.reconfigure()
        if "tts_voice" in updates:
            tts_manager.set_voice(updates["tts_voice"])
        if "tts_speed" in updates:
            tts_manager.set_speed(updates["tts_speed"])
        if "tts_volume" in updates:
            tts_manager.set_volume(updates["tts_volume"])

    # Return the full updated settings so the frontend stays in sync
    s2 = get_settings()
    db_settings2 = memory_manager.store.get_all_settings()
    return {
        "assistant_name": s2.assistant_name,
        "user_name": s2.user_name,
        "voice_enabled": s2.voice_enabled,
        "voice_language": s2.voice_language,
        "tts_enabled": s2.tts_enabled,
        "tts_voice": s2.tts_voice,
        "tts_speed": s2.tts_speed,
        "tts_volume": s2.tts_volume,
        "wake_word_enabled": s2.wake_word_enabled,
        "wake_word": s2.wake_word,
        "memory_enabled": s2.memory_enabled,
        "vector_memory_enabled": s2.vector_memory_enabled,
        "message_notifications_enabled": s2.message_notifications_enabled,
        "browser_notifications_enabled": s2.browser_notifications_enabled,
        "voice_notifications_enabled": s2.voice_notifications_enabled,
        "desktop_notifications_enabled": s2.desktop_notifications_enabled,
        "debug": s2.debug,
        "groq_model": s2.groq_model,
        "groq_api_key": _mask_api_key(s2.groq_api_key),
        "gemini_api_key": _mask_api_key(s2.gemini_api_key),
        "gemini_model": s2.gemini_model,
        "openrouter_api_key": _mask_api_key(s2.openrouter_api_key),
        "openrouter_model": s2.openrouter_model,
        "local_llm_url": s2.local_llm_url,
        "local_llm_model": s2.local_llm_model,
        "local_llm_enabled": s2.local_llm_enabled,
        "local_llm_api_key": _mask_api_key(s2.local_llm_api_key),
        "local_llm_api_type": s2.local_llm_api_type,
        "local_llm_timeout": s2.local_llm_timeout,
        "tts_engine": s2.tts_engine,
        "response_style": s2.response_style,
        "language": s2.language,
        "auto_failover": s2.auto_failover,
        "provider_priority": s2.provider_priority,
        "theme": s2.theme,
        "accent_color": s2.accent_color,
        "glow_intensity": s2.glow_intensity,
        "animation_level": s2.animation_level,
        "orb_size": s2.orb_size,
        "persona": s2.persona,
        "compact_ui": getattr(s2, "compact_ui", False),
        "panel_transparency": getattr(s2, "panel_transparency", 85),
        "background_particles": getattr(s2, "background_particles", True),
        "reduced_motion": getattr(s2, "reduced_motion", False),
        "font_size": getattr(s2, "font_size", "normal"),
        "language_mode": getattr(s2, "language_mode", "auto"),
        "image_generation_enabled": getattr(s2, "image_generation_enabled", True),
        "image_provider": getattr(s2, "image_provider", "auto"),
        "pixazo_api_key": _mask_api_key(getattr(s2, "pixazo_api_key", "")),
        "puter_api_key": _mask_api_key(getattr(s2, "puter_api_key", "")),
        "video_generation_enabled": getattr(s2, "video_generation_enabled", True),
        "video_provider": getattr(s2, "video_provider", "auto"),
        "fal_api_key": _mask_api_key(getattr(s2, "fal_api_key", "")),
        "magic_hour_api_key": _mask_api_key(getattr(s2, "magic_hour_api_key", "")),
        "gesture_control_enabled": getattr(s2, "gesture_control_enabled", False),
        "gesture_camera_device": getattr(s2, "gesture_camera_device", ""),
        "gesture_sensitivity": getattr(s2, "gesture_sensitivity", 50),
        "call_control_enabled": getattr(s2, "call_control_enabled", False),
        "call_provider": getattr(s2, "call_provider", ""),
        "call_assist_mode": getattr(s2, "call_assist_mode", "notify_only"),
        "vision_enabled": getattr(s2, "vision_enabled", False),
        "vision_provider": getattr(s2, "vision_provider", ""),
        "vision_confidence_threshold": getattr(s2, "vision_confidence_threshold", 0.70),
        "vision_local_model": getattr(s2, "vision_local_model", ""),
        "vision_cloud_model": getattr(s2, "vision_cloud_model", ""),
        "vision_max_retries": getattr(s2, "vision_max_retries", 3),
        "vision_cache_ttl": getattr(s2, "vision_cache_ttl", 30.0),
        "vision_capture_hotkey": getattr(s2, "vision_capture_hotkey", "ctrl+shift+j"),
        "research_max_sources": getattr(s2, "research_max_sources", 20),
        "research_depth": getattr(s2, "research_depth", "deep"),
        "research_document_format": getattr(s2, "research_document_format", "markdown"),
        "agent_enabled": getattr(s2, "agent_enabled", True),
        "agent_auto_execute": getattr(s2, "agent_auto_execute", False),
        "agent_auto_fix": getattr(s2, "agent_auto_fix", True),
        "agent_max_retries": getattr(s2, "agent_max_retries", 3),
        "agent_confirmation_level": getattr(s2, "agent_confirmation_level", "risky_only"),
        "agent_terminal": getattr(s2, "agent_terminal", "ask"),
        "agent_filesystem_delete": getattr(s2, "agent_filesystem_delete", "ask"),
        "agent_network": getattr(s2, "agent_network", "ask"),
        "agent_git": getattr(s2, "agent_git", "ask"),
        "browser_enabled": getattr(s2, "browser_enabled", True),
        "browser_engine": getattr(s2, "browser_engine", "chromium"),
        "browser_mode": getattr(s2, "browser_mode", "visible"),
        "browser_profile": getattr(s2, "browser_profile", "isolated"),
        "browser_download_dir": getattr(s2, "browser_download_dir", "~/Downloads/JARVIS-Browser"),
        "browser_search_engine": getattr(s2, "browser_search_engine", "https://www.google.com"),
        "browser_permission": getattr(s2, "browser_permission", "ask"),
        "browser_timeout": getattr(s2, "browser_timeout", 30),
        "browser_max_retries": getattr(s2, "browser_max_retries", 3),
        "computer_enabled": getattr(s2, "computer_enabled", True),
        "computer_mode": getattr(s2, "computer_mode", "off"),
        "computer_screen_access": getattr(s2, "computer_screen_access", "ask"),
        "computer_mouse_control": getattr(s2, "computer_mouse_control", "ask"),
        "computer_keyboard_control": getattr(s2, "computer_keyboard_control", "ask"),
        "computer_application_launch": getattr(s2, "computer_application_launch", "ask"),
        "computer_window_control": getattr(s2, "computer_window_control", "ask"),
        "computer_screen_preview": getattr(s2, "computer_screen_preview", "off"),
        "computer_mouse_failsafe": getattr(s2, "computer_mouse_failsafe", True),
        "computer_max_retries": getattr(s2, "computer_max_retries", 3),
        "db_settings": db_settings2,
    }
