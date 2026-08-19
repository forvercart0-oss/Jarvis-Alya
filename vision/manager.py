"""Vision manager for JARVIS Phase 14."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from vision.analyzer import analyze_image, describe_screen
from vision.audit import vision_audit
from vision.camera import CameraManager
from vision.capture import capture_screen, get_active_window, get_screen_info, list_monitors
from vision.comparison import compare_images
from vision.detector import detect_elements, find_target
from vision.image_utils import validate_image
from vision.ocr import ocr_image
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
        self._camera = CameraManager()
        self._screen_intelligence = None

    def _get_screen_intelligence(self):
        if self._screen_intelligence is None:
            from vision.screen_intelligence import screen_intelligence
            screen_intelligence.confidence_threshold = self.confidence_threshold
            screen_intelligence.set_broadcast(self._broadcast)
            self._screen_intelligence = screen_intelligence
        return self._screen_intelligence

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    @property
    def camera_active(self) -> bool:
        return self._camera.active

    def set_broadcast(self, broadcast: Any) -> None:
        self._broadcast = broadcast
        if self._screen_intelligence:
            self._screen_intelligence.set_broadcast(broadcast)

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
        try:
            from config.settings import get_settings
            settings = get_settings()
            external_allowed = getattr(settings, "vision_external_provider_allowed", True)
        except Exception:
            external_allowed = True
        for p in self._providers:
            try:
                is_local = getattr(p, "name", "") in ("local", "local_vision", "mock")
                if not external_allowed and not is_local:
                    continue
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    health = None
                else:
                    health = loop.run_until_complete(p.health_check())
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
            vision_audit.log("screenshot_denied", {"mode": mode, "permission": perm.get("permission")})
            return {"success": False, "error": "Permission denied: vision.capture"}

        start = time.time()
        result = await capture_screen(mode, window, parse_region(region) if region else None, monitor)
        latency = time.time() - start
        result["latency_ms"] = round(latency * 1000)
        if result.get("ok") or result.get("success"):
            self._last_capture = result
            await self._broadcast_event("vision_capture", {"mode": mode, "latency_ms": result["latency_ms"]})
            vision_audit.log("screenshot", {"mode": mode, "latency_ms": result["latency_ms"], "success": True})
        else:
            vision_audit.log("screenshot", {"mode": mode, "success": False, "error": result.get("error")})
        return result

    async def analyze(self, image_path: str, prompt: str = "", mode: str = "describe") -> dict[str, Any]:
        if not self._enabled:
            return {"success": False, "error": "Vision is disabled."}
        from vision.permissions import vision_analyze
        perm = await vision_analyze()
        if not perm.get("allowed"):
            vision_audit.log("analyze_denied", {"mode": mode, "permission": perm.get("permission")})
            return {"success": False, "error": "Permission denied: vision.analyze"}

        try:
            validate_image(image_path)
        except Exception as exc:
            vision_audit.log("analyze_validation_failed", {"mode": mode, "error": str(exc)})
            return {"success": False, "error": str(exc)}

        cache_key = f"{mode}:{image_path}:{prompt}"
        cached = self._cache.get(cache_key)
        if cached and (time.time() - cached["ts"]) < self._cache_ttl:
            vision_audit.log("analyze_cache_hit", {"mode": mode})
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
        await self._broadcast_event(
            "vision_analysis_completed",
            {"mode": mode, "latency_ms": result["latency_ms"], "success": result.get("success")},
        )
        vision_audit.log(
            "analyze",
            {"mode": mode, "latency_ms": result["latency_ms"], "success": result.get("success")},
        )
        return result

    async def compare(self, image_a: str, image_b: str) -> dict[str, Any]:
        if not self._enabled:
            return {"success": False, "error": "Vision is disabled."}
        try:
            validate_image(image_a)
            validate_image(image_b)
        except Exception as exc:
            vision_audit.log("compare_validation_failed", {"error": str(exc)})
            return {"success": False, "error": str(exc)}
        result = await compare_images(image_a, image_b)
        await self._broadcast_event("vision_compare_completed", {"identical": result.get("identical")})
        vision_audit.log("compare", {"identical": result.get("identical"), "success": result.get("success")})
        return result

    async def camera_start(self) -> dict[str, Any]:
        from vision.permissions import vision_capture
        perm = await vision_capture()
        if not perm.get("allowed"):
            vision_audit.log("camera_start_denied", {"permission": perm.get("permission")})
            return {"success": False, "error": "Permission denied: vision.capture"}
        result = await self._camera.start()
        await self._broadcast_event("camera_started", result)
        vision_audit.log("camera_start", {"success": result.get("success")})
        return result

    async def camera_stop(self) -> dict[str, Any]:
        result = await self._camera.stop()
        await self._broadcast_event("camera_stopped", result)
        vision_audit.log("camera_stop", {"success": result.get("success")})
        return result

    async def camera_capture(self) -> dict[str, Any]:
        return await self._camera.capture()

    async def find(self, target: str, region: str | None = None) -> dict[str, Any]:
        if not self._enabled:
            return {"success": False, "error": "Vision is disabled."}
        from vision.permissions import vision_analyze
        perm = await vision_analyze()
        if not perm.get("allowed"):
            vision_audit.log("find_denied", {"target": target, "permission": perm.get("permission")})
            return {"success": False, "error": "Permission denied: vision.analyze"}

        capture = await self.screenshot("full" if not region else "region", region=region)
        if not capture.get("ok") and not capture.get("success"):
            vision_audit.log("find_capture_failed", {"target": target, "error": capture.get("error")})
            return capture
        result = await find_target(capture["path"], target)
        if result.get("found"):
            await self._broadcast_event("vision_target_found", {
                "target": target, "x": result.get("x"), "y": result.get("y"),
                "confidence": result.get("confidence"),
            })
        vision_audit.log("find", {
            "target": target, "found": result.get("found"),
            "confidence": result.get("confidence"),
        })
        return result

    async def remember_visual(
        self,
        image_path: str,
        description: str,
        tags: list[str] | None = None,
        project: str = "",
        source: str = "explicit_user",
    ) -> dict[str, Any]:
        if not self._enabled:
            return {"success": False, "error": "Vision is disabled."}
        try:
            validate_image(image_path)
        except Exception as exc:
            return {"success": False, "error": str(exc)}
        try:
            from memory.sqlite_memory import SqliteMemory
            mem = SqliteMemory()
            tags = tags or []
            tags.append("visual")
            result = mem.remember(
                content=description,
                category="visual",
                source=source,
                project=project,
                tags=tags,
                importance=0.7,
                memory_type="observation",
            )
            vision_audit.log("remember_visual", {"memory_id": result.get("id"), "tags": tags})
            return {"success": True, "memory_id": result.get("id"), "description": description}
        except Exception as exc:
            logger.warning("Failed to store visual memory: %s", exc)
            return {"success": False, "error": str(exc)}

    async def active_window(self) -> dict[str, Any]:
        return await get_active_window()

    async def screen_info(self) -> dict[str, Any]:
        return await get_screen_info()

    async def monitors(self) -> list[dict[str, Any]]:
        return await list_monitors()

    async def screen_intelligence_capture(self, mode: str = "full", window: str | None = None, region: str | None = None, monitor: int | None = None) -> dict[str, Any]:
        si = self._get_screen_intelligence()
        return await si.capture_and_understand(mode, window, region, monitor)

    async def screen_intelligence_command(self, command: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        si = self._get_screen_intelligence()
        return await si.execute_command(command, context)

    async def screen_intelligence_status(self) -> dict[str, Any]:
        si = self._get_screen_intelligence()
        return {"enabled": si.enabled, "mode": si.mode}

    async def screen_intelligence_set_mode(self, mode: str) -> dict[str, Any]:
        si = self._get_screen_intelligence()
        si.mode = mode
        si.enabled = mode != "off"
        return {"success": True, "mode": mode, "enabled": si.enabled}

    async def understand_application(self, window_title: str = "", ocr_text: str = "") -> dict[str, Any]:
        if not self._enabled:
            return {"success": False, "error": "Vision is disabled."}
        try:
            from vision.application_understanding import application_understanding
            detection = application_understanding.detect_application(window_title, ocr_text)
            context = application_understanding.get_application_context(detection.get("application", "unknown"), ocr_text)
            return {"success": True, "detection": detection, "context": context}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def detect_dialog(self, ocr_text: str, window_title: str = "") -> dict[str, Any]:
        try:
            from vision.dialog_detection import dialog_detector
            result = dialog_detector.detect(ocr_text, window_title)
            if result:
                return {"success": True, "dialog": result.to_dict()}
            return {"success": True, "dialog": None}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def start_workflow_recording(self, name: str = "") -> dict[str, Any]:
        try:
            from vision.workflow_recorder import workflow_recorder
            workflow = workflow_recorder.start(name)
            return {"success": True, "workflow": workflow.to_dict()}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def stop_workflow_recording(self) -> dict[str, Any]:
        try:
            from vision.workflow_recorder import workflow_recorder
            workflow = workflow_recorder.stop()
            if workflow:
                return {"success": True, "workflow": workflow.to_dict()}
            return {"success": False, "error": "No active recording"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def replay_workflow(self, workflow: dict[str, Any], re_detect: bool = True) -> dict[str, Any]:
        if not self._enabled:
            return {"success": False, "error": "Vision is disabled."}
        try:
            from vision.workflow_replay import workflow_replayer
            return await workflow_replayer.replay(workflow, re_detect)
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def load_visual_skills(self) -> dict[str, Any]:
        try:
            from vision.visual_skills import visual_skill_manager
            visual_skill_manager.load_skills()
            return {"success": True, "skills": visual_skill_manager.list_skills()}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def match_visual_skill(self, text: str) -> dict[str, Any]:
        try:
            from vision.visual_skills import visual_skill_manager
            skill = visual_skill_manager.find_by_trigger(text)
            if skill:
                return {"success": True, "skill": skill.to_dict()}
            return {"success": True, "skill": None}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def gesture_start(self) -> dict[str, Any]:
        try:
            from vision.gesture.controller import GestureController
            from config.settings import get_settings
            settings = get_settings()
            controller = GestureController(settings)
            result = await controller.start()
            return {"success": True, "gesture_active": result}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def gesture_stop(self) -> dict[str, Any]:
        try:
            from vision.gesture.controller import GestureController
            controller = GestureController(None)
            result = await controller.stop()
            return {"success": True, "gesture_active": result}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self._enabled,
            "provider": self._active_provider.name if self._active_provider else None,
            "providers": len(self._providers),
            "last_capture": self._last_capture,
            "confidence_threshold": self.confidence_threshold,
            "camera_active": self._camera.active,
        }


vision_manager = VisionManager()
