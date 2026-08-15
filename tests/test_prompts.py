from brain.prompts import build_system_prompt


def test_system_prompt_contains_name():
    prompt = build_system_prompt("JARVIS", "Sir")
    assert "JARVIS" in prompt
    assert "Sir" in prompt


def test_system_prompt_mentions_tools():
    prompt = build_system_prompt()
    assert "open_application" in prompt
    assert "cpu_usage" in prompt
    assert "get_cpu_usage" not in prompt
