import asyncio
import logging
from datetime import datetime, time as dtime
from typing import Any, Optional

from memory.manager import MemoryManager
from backend.services.ws_manager import ws_manager

logger = logging.getLogger("jarvis.automation")


class AutomationService:
    """Runs scheduled / keyword / startup automations and fires their actions."""

    def __init__(self, memory: MemoryManager, speak_callback=None, command_callback=None):
        self.memory = memory
        self.store = memory.store
        self._speak = speak_callback
        self._command = command_callback
        self._task: Optional[asyncio.Task] = None
        self._startup_fired: set[str] = set()
        self._last_fired: dict[str, str] = {}
        self._running = False

    def _parse_time(self, schedule: str) -> Optional[str]:
        """Return 'HH:MM' if schedule matches a daily time (HH:MM or HH:MM:SS)."""
        if not schedule:
            return None
        s = schedule.strip()
        try:
            if s.count(":") == 1:
                dtime.fromisoformat(s)
                return s
            if s.count(":") == 2:
                parts = s.split(":")
                dtime(int(parts[0]), int(parts[1]), int(parts[2]))
                return f"{parts[0]}:{parts[1]}"
        except ValueError:
            return None
        return None

    async def _fire(self, automation: dict) -> None:
        action = automation.get("action", "")
        payload = automation.get("action_payload", {}) or {}
        logger.info("Firing automation '%s' (trigger=%s)", automation.get("name"), automation.get("trigger"))
        if action == "speak":
            text = payload.get("text", f"{automation.get('name', 'Automation')} triggered.")
            if self._speak:
                await self._speak(text)
        elif action == "command":
            cmd = payload.get("command", "")
            if cmd and self._command:
                await self._command(cmd)
        elif action == "notification":
            message = payload.get("message", f"{automation.get('name', 'Automation')} triggered.")
            await ws_manager.broadcast("notification", {"message": message, "type": payload.get("type", "info")})
        else:
            await ws_manager.broadcast("automation_triggered", {
                "name": automation.get("name"),
                "action": action,
                "payload": payload,
            })

    def _due_time_automation(self, automation: dict) -> bool:
        schedule = automation.get("schedule")
        match = self._parse_time(schedule)
        if match is None:
            return False
        now = datetime.now().strftime("%H:%M")
        if now != match:
            return False
        key = automation.get("id", automation.get("name", ""))
        if self._last_fired.get(key) == now:
            return False
        self._last_fired[key] = now
        return True

    async def check_keyword(self, text: str) -> None:
        if not text:
            return
        lowered = text.lower()
        for automation in self.store.get_automations():
            if automation.get("trigger") != "keyword":
                continue
            keywords = automation.get("keywords", []) or []
            if any(k.lower() in lowered for k in keywords):
                await self._fire(automation)

    async def check_startup(self) -> None:
        for automation in self.store.get_automations():
            if automation.get("trigger") != "startup":
                continue
            aid = automation.get("id", "")
            if aid in self._startup_fired:
                continue
            self._startup_fired.add(aid)
            await self._fire(automation)

    async def _tick(self):
        while self._running:
            try:
                for automation in self.store.get_automations():
                    if not automation.get("enabled", True):
                        continue
                    if automation.get("trigger") == "time" and self._due_time_automation(automation):
                        await self._fire(automation)
            except Exception as exc:
                logger.warning("Automation tick failed: %s", exc)
            await asyncio.sleep(20)

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._tick())
        await self.check_startup()

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
            self._task = None


def parse_automation_payload(data: dict) -> dict:
    """Normalize an automation dict, parsing comma-separated keywords."""
    result = dict(data)
    if "action_payload" in result and isinstance(result["action_payload"], str):
        import json

        try:
            result["action_payload"] = json.loads(result["action_payload"])
        except Exception:
            result["action_payload"] = {}
    keywords = result.get("keywords")
    if isinstance(keywords, str):
        result["keywords"] = [k.strip() for k in keywords.split(",") if k.strip()]
    return result
