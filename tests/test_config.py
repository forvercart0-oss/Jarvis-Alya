from config.settings import Settings, get_settings


def test_settings_defaults():
    settings = Settings(_env_file=None)
    assert settings.assistant_name == "JARVIS"
    assert settings.wake_word_enabled is False
    assert settings.gemini_model == "gemini-2.0-flash"


def test_get_settings_singleton():
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
