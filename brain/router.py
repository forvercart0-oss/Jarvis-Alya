import re
from brain.groq_client import GroqClient
from brain.offline import offline_reply


class Route:
    def __init__(self, action: str, name: str, arguments: dict):
        self.action = action
        self.name = name
        self.arguments = arguments


class Router:
    def __init__(self, groq=None):
        self.groq = groq

    def heuristic_route(self, text: str) -> Route:
        lower = text.lower()

        if "remember" in lower and ("my favorite" in lower or "that" in lower):
            content = re.sub(r"^remember\s+(that\s+)?", "", text, flags=re.IGNORECASE).strip()
            return Route("tool", "remember", {"content": content})

        if "forget" in lower:
            query = re.sub(r"^forget\s+(that\s+)?", "", text, flags=re.IGNORECASE).strip()
            return Route("tool", "forget", {"query": query})

        if lower.startswith("open ") or "launch" in lower:
            if "http" in lower or "www" in lower:
                url = re.search(r"(https?://\S+|www\.\S+)", text)
                return Route("tool", "open_browser", {"url": url.group(1) if url else text})
            app = lower.replace("open", "").replace("launch", "").strip()
            return Route("tool", "open_application", {"app_name": app})

        if "search the web" in lower or "search for" in lower:
            query = lower.replace("search the web for", "").replace("search for", "").strip()
            return Route("tool", "web_search", {"query": query})

        if "cpu" in lower or "processor" in lower:
            return Route("tool", "cpu_usage", {})

        if "memory" in lower and ("usage" in lower or "ram" in lower or "using my ram" in lower):
            return Route("tool", "memory_usage", {})

        if "disk" in lower or "storage" in lower:
            return Route("tool", "disk_usage", {})

        if "battery" in lower:
            return Route("tool", "battery_status", {})

        if re.search(r"\bwhat\s+time\b", lower) or lower.strip() == "what time is it":
            return Route("tool", "get_time", {})

        if re.search(r"\bwhat\s+date\b", lower) or lower.strip() == "what is the date":
            return Route("tool", "get_date", {})

        if "calculate" in lower or "times" in lower or "plus" in lower or "minus" in lower or "divided" in lower:
            expr = lower.replace("calculate", "").replace("times", "*").replace("plus", "+").replace("minus", "-").replace("divided by", "/").replace(" ", "").strip()
            return Route("tool", "calculator", {"expression": expr})

        if "volume" in lower:
            level = re.search(r"(\d+)", text)
            return Route("tool", "volume_control", {"level": int(level.group(1)) if level else None})

        if "lock" in lower and "computer" in lower:
            return Route("tool", "lock_screen", {})

        if "reboot" in lower:
            return Route("tool", "reboot", {})

        if "shutdown" in lower:
            return Route("tool", "shutdown", {})

        if "suspend" in lower:
            return Route("tool", "suspend", {})

        if "read " in lower and ("/" in lower or ".txt" in lower):
            path = re.search(r"(/[\w/\.]+)", text)
            return Route("tool", "read_file", {"path": path.group(1) if path else text.replace("read", "").strip()})

        if "hello" in lower or "hi" in lower:
            return Route("respond", "", {})

        return Route("respond", "", {})

    async def decide(self, messages: list[dict]) -> Route:
        groq = self.groq
        available = bool(groq and hasattr(groq, "is_available") and groq.is_available())
        if not available:
            last = messages[-1]["content"] if messages else ""
            return self.heuristic_route(last)
        return Route("respond", "", {})
