"""Offline fallback responses when the Groq API is unreachable.

These replies are clearly generic and never pretend to be an AI answer from
Groq. They acknowledge what was done (from the real tool result) and tell the
user the cloud brain is offline.
"""

from __future__ import annotations

from typing import Any

_OPEN_APP_NAMES = {
    "firefox": "Firefox",
    "konsole": "Konsole",
    "code": "VS Code",
    "dolphin": "Dolphin",
    "vlc": "VLC",
    "spotify": "Spotify",
    "discord": "Discord",
}

_DANGEROUS_CONFIRM = 'That action requires confirmation, Sir. Say "yes" to proceed or "no" to cancel.'


def offline_reply(
    user_input: str, route: dict[str, Any] | None = None, tool_result: dict[str, Any] | None = None
) -> str:
    """Produce a truthful, helpful offline reply from a real tool result."""
    text = (user_input or "").strip().lower()
    tool = (route or {}).get("name") if route else None

    if tool_result and tool_result.get("confirmation_required"):
        return _DANGEROUS_CONFIRM

    if tool_result and not tool_result.get("success"):
        return f"Sir, that operation did not succeed: {tool_result.get('error', 'unknown error')}."

    if tool == "open_application" and tool_result and tool_result.get("success"):
        app = (tool_result.get("result") or {}).get("application", "")
        display = _OPEN_APP_NAMES.get(app, app.title() if app else "it")
        return f"Certainly, Sir. {display} has been launched."

    if tool == "get_time":
        return f"The time is {tool_result['result'].get('time')}, Sir."

    if tool == "get_date":
        r = tool_result["result"]
        return f"Today is {r.get('weekday')}, {r.get('date')}, Sir."

    if tool == "cpu_usage":
        return f"CPU usage is currently {tool_result['result'].get('cpu_percent')} percent, Sir."

    if tool == "memory_usage":
        r = tool_result["result"]
        return f"RAM usage is {r.get('percent')} percent ({r.get('used_gb')} of {r.get('total_gb')} GB), Sir."

    if tool == "disk_usage":
        r = tool_result["result"]
        return f"Disk {r.get('path')} is {r.get('percent')} percent full, Sir."

    if tool == "battery_status":
        r = tool_result.get("result", {})
        if r.get("status") == "No battery detected":
            return "No battery is detected on this system, Sir."
        return f"Battery is at {r.get('percent')} percent and is {'plugged in' if r.get('power_plugged') else 'on battery'}, Sir."

    if tool == "calculator":
        return f"The result is {tool_result['result'].get('result')}, Sir."

    if tool == "remember" and tool_result and tool_result.get("success"):
        return "Consider it done, Sir. I have stored that."

    if tool == "recall_memories" and tool_result and tool_result.get("success"):
        mems = (tool_result.get("result") or {}).get("memories", [])
        if not mems:
            return "I don't seem to have any memories stored yet, Sir."
        lines = "\n".join(f"- {m['value']}" for m in mems[:8])
        return f"Here is what I remember, Sir:\n{lines}"

    if "hello" in text or "hi " in text or text == "hi" or "good morning" in text or "good evening" in text:
        return "Good to see you, Sir. I'm running in offline mode right now - how can I assist?"

    if "how are you" in text:
        return "All systems nominal, Sir. I'm running in offline mode as the cloud brain is unreachable."

    if "who are you" in text:
        return "I am JARVIS 2.0, your desktop assistant, Sir. The cloud brain is currently offline."

    return (
        "Sir, I'm running in offline mode because the Groq service is "
        "unreachable. I can still answer basic system questions and run safe "
        "local tools. Please check your internet connection and API key."
    )
