"""Vision manager for JARVIS Phase 4."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from vision.analyzer import analyze_image, describe_screen
from vision.capture import capture_screen, get_active_window, get_screen_info, list_monitors
from vision.detector import detect_elements, find_target
from vision.ocr import ocr_image, ocr_region
from vision.regions import parse_region

logger = logging.getLogger("jarvis.vision.manager")


class VisionManager:
    def __init__(self):
        self._enabled: bool = False
        self._providers: list[Any] = []
        self._active_provider: Any = None
        self.confidence_threshold: float = 0.70
        self._last_capture: dict[str, Any] | None = None
        self._cache: dict[str, Any] = {}
        self._cache_ttl: float = 30.0
        self._broadcast: Any = None

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    def set_broadcast(self, broadcast: Any) -> None:
        self._broadcast = broadcast

    async def _broadcast_event(self, event: str, data: dict[str, Any]) -> None:
        if self._broadcast:
            try:
                await self._broadcast(event, data)
            except Exception:
                pass

    def register_provider(self, provider: Any) -> None:
        self._providers.append(provider)

    def get_provider(self) -> Any | None:
        if self._active_provider:
            return self._active_provider
        for p in self._providers:
            try:
                health = asyncio.get_event_loop().run_until_complete(p.health_check()) if not asyncio.get_event_loop().is_running() else None
                if health and health.get("status") == "online":
                    self._active_provider = p
                    return p
            except Exception:
                continue
        if self._providers:
            self._active_provider = self._providers[0]
            return self._providers[0]
        return None

    async def screenshot(
        self,
        mode: str = "full",
        window: str | None = None,
        region: str | None = None,
        monitor: int | None = None,
    ) -> dict[str, Any]:
        if not self._enabled:
            return {"success": False, "error": "Vision is disabled."}
        from vision.permissions import vision_capture
        perm = await vision_capture()
        if not perm.get("allowed"):
            return {"success": False, "error": "Permission denied: vision.capture"}

        start = time.time()
        result = await capture_screen(mode, window, parse_region(region) if region else None, monitor)
        latency = time.time() - start
        result["latency_ms"] = round(latency * 1000)
        if result.get("ok") or result.get("success"):
            self._last_capture = result
            await self._broadcast_event("vision_capture", {"mode": mode, "latency_ms": result["latency_ms"]})
        return result

    async def analyze(
        self,
        image_path: str,
        prompt: str = "",
        mode: str = "describe",
    ) -> dict[str, Any]:
        if not self._enabled:
            return {"success": False, "error": "Vision is disabled."}
        from vision.permissions import vision_analyze
        perm = await vision_analyze()
        if not perm.get("allowed"):
            return {"success": False, "error": "Permission denied: vision.analyze"}

        cache_key = f"{mode}:{image_path}:{prompt}"
        cached = self._cache.get(cache_key)
        if cached and (time.time() - cached["ts"]) < self._cache_ttl:
            return cached["data"]

        await self._broadcast_event("vision_analysis_started", {"mode": mode, "image": image_path})
        start = time.time()
        if mode == "describe":
            result = await describe_screen(image_path)
        elif mode == "ocr":
            result = await ocr_image(image_path)
        elif mode == "elements":
            result = await detect_elements(image_path)
        else:
            result = await analyze_image(image_path, prompt)

        latency = time.time() - start
        result["latency_ms"] = round(latency * 1000)
        self._cache[cache_key] = {"ts": time.time(), "data": result}
        await self._broadcast_event("vision_analysis_completed", {"mode": mode, "latency_ms": result["latency_ms"], "success": result.get("success")})
        return result

    async def find(self, target: str, region: str | None = None) -> dict[str, Any]:
        if not self._enabled:
            return {"success": False, "error": "Vision is disabled."}
        from vision.permissions import vision_analyze
        perm = await vision_analyze()
        if not perm.get("allowed"):
            return {"success": False, "error": "Permission denied: vision.analyze"}

        capture = await self.screenshot("full" if not region else "region", region=region)
        if not capture.get("ok") and not capture.get("success"):
            return capture
        result = await find_target(capture["path"], target)
        if result.get("found"):
            await self._broadcast_event("vision_target_found", {"target": target, "x": result.get("x"), "y": result.get("y"), "confidence": result.get("confidence")})
        return result

    async def active_window(self) -> dict[str, Any]:
        return await get_active_window()

    async def screen_info(self) -> dict[str, Any]:
        return await get_screen_info()

    async def monitors(self) -> list[dict[str, Any]]:
        return await list_monitors()

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self._enabled,
            "provider": self._active_provider.name if self._active_provider else None,
            "providers": len(self._providers),
            "last_capture": self._last_capture,
            "confidence_threshold": self.confidence_threshold,
        }


vision_manager = VisionManager()
