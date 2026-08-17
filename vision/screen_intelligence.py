"""Screen intelligence orchestrator for JARVIS Phase 24.

Orchestrates the screen intelligence pipeline:
ScreenCapture -> ImagePreprocessor -> VisionAnalyzer -> OCR -> UIElementDetector
-> ScreenUnderstanding -> ActionPlanner -> ComputerAutomation -> Verification
"""

from __future__ import annotations

import logging
import time
from contextlib import suppress
from typing import Any

from vision.action_log import ActionLogEntry

logger = logging.getLogger("jarvis.vision.screen_intelligence")


class ScreenIntelligenceMode:
    OFF = "off"
    ON_DEMAND = "on_demand"
    CONTINUOUS = "continuous"


class ScreenIntelligenceOrchestrator:
    def __init__(self):
        self._mode = ScreenIntelligenceMode.ON_DEMAND
        self._enabled = False
        self._continuous_task = None
        self._last_capture_path: str | None = None
        self._last_understanding = None
        self._understanding_engine = None
        self._planner = None
        self._verifier = None
        self._diff_engine = None
        self._action_logger = None
        self._broadcast = None
        self._confidence_threshold = 0.70
        self._max_retries = 3
        self._current_attempt: dict[str, int] = {}

    def set_broadcast(self, broadcast: Any) -> None:
        self._broadcast = broadcast

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        self._mode = value

    def _get_understanding_engine(self):
        if self._understanding_engine is None:
            from vision.screen_understanding import screen_understanding_engine
            self._understanding_engine = screen_understanding_engine
        return self._understanding_engine

    def _get_planner(self):
        if self._planner is None:
            from vision.action_planner import visual_action_planner
            self._planner = visual_action_planner
        return self._planner

    def _get_verifier(self):
        if self._verifier is None:
            from vision.action_verification import action_verifier
            self._verifier = action_verifier
        return self._verifier

    def _get_diff_engine(self):
        if self._diff_engine is None:
            from vision.screen_diff import screen_diff_engine
            self._diff_engine = screen_diff_engine
        return self._diff_engine

    def _get_action_logger(self):
        if self._action_logger is None:
            from vision.action_log import action_logger
            self._action_logger = action_logger
        return self._action_logger

    async def _broadcast(self, event: str, data: dict[str, Any]) -> None:
        if self._broadcast:
            with suppress(Exception):
                await self._broadcast(event, data)

    async def capture_and_understand(
        self,
        mode: str = "full",
        window: str | None = None,
        region: str | None = None,
        monitor: int | None = None,
    ) -> dict[str, Any]:
        if not self._enabled:
            return {"success": False, "error": "Screen intelligence is disabled"}

        await self._broadcast("screen_capture_started", {"mode": mode})
        start = time.time()

        try:
            import os
            import tempfile

            from vision.capture import capture_screen
            fd, output_path = tempfile.mkstemp(suffix=".png")
            os.close(fd)
            capture_result = await capture_screen(mode, window, region, monitor, output_path)
            if not capture_result.get("ok") and not capture_result.get("success"):
                err = capture_result.get("error", "Capture failed")
                await self._broadcast("screen_capture_complete", {"success": False, "error": err})
                return {"success": False, "error": err}

            self._last_capture_path = output_path

            with suppress(Exception):
                from vision.image_utils import preprocess_image
                preprocess_image(output_path)

            await self._broadcast("screen_analysis_started", {"image": output_path})
            understanding = await self._get_understanding_engine().understand(output_path, mode, monitor, window)
            self._last_understanding = understanding

            latency = time.time() - start
            await self._broadcast("screen_analysis_complete", {
                "success": True,
                "latency_ms": round(latency * 1000),
                "application": understanding.application,
                "description": understanding.description,
            })

            return {
                "success": True,
                "image_path": output_path,
                "understanding": understanding.to_dict(),
                "latency_ms": round(latency * 1000),
            }
        except Exception as exc:
            logger.error("Screen intelligence pipeline failed: %s", exc)
            await self._broadcast("screen_analysis_complete", {"success": False, "error": str(exc)})
            return {"success": False, "error": str(exc)}

    async def execute_command(self, text: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self._enabled:
            return {"success": False, "error": "Screen intelligence is disabled"}

        plan = self._get_planner().plan(text)
        if not plan.actions:
            return {"success": False, "error": "Could not understand command", "plan": plan.to_dict()}

        results = []
        for action in plan.actions:
            if action.confidence < self._confidence_threshold:
                results.append({
                    "action": action.to_dict(),
                    "result": {"success": False, "error": f"Low confidence: {action.confidence}"},
                })
                continue

            key = action.action_type
            attempt_count = self._current_attempt.get(key, 0)
            if attempt_count >= self._max_retries:
                results.append({
                    "action": action.to_dict(),
                    "result": {"success": False, "error": "Max retries exceeded"},
                })
                continue

            await self._broadcast("visual_action_started", {
                "action": action.action_type,
                "arguments": action.arguments,
            })

            action_start = time.time()
            result = await self._execute_action(action)
            duration = time.time() - action_start

            self._get_action_logger().log(
                ActionLogEntry(
                    action=action.action_type,
                    target=action.arguments.get("target", ""),
                    arguments=action.arguments,
                    result=str(result.get("result", result.get("error", ""))),
                    confidence=action.confidence,
                    duration_ms=round(duration * 1000),
                    success=result.get("success", False),
                    application=self._last_understanding.application if self._last_understanding else "",
                )
            )

            if result.get("success") and action.requires_verification:
                verified = await self._get_verifier().verify_click(
                    action.arguments.get("x", 0),
                    action.arguments.get("y", 0),
                    action.expected_state,
                )
                if not verified.get("verified"):
                    self._current_attempt[key] = attempt_count + 1
                    result["verification"] = "failed"
                else:
                    self._current_attempt[key] = 0
                    result["verification"] = "passed"
            elif result.get("success"):
                self._current_attempt[key] = 0

            if result.get("success"):
                await self._broadcast("visual_action_complete", {
                    "action": action.action_type,
                    "result": result,
                })
            else:
                await self._broadcast("visual_action_failed", {
                    "action": action.action_type,
                    "error": result.get("error"),
                })

            results.append({"action": action.to_dict(), "result": result})

        return {
            "success": all(r["result"].get("success", False) for r in results),
            "plan": plan.to_dict(),
            "results": results,
        }

    async def _execute_action(self, action: Any) -> dict[str, Any]:
        action_type = action.action_type
        args = action.arguments

        if action_type == "find_and_click":
            return await self._find_and_click(args.get("target", ""))
        if action_type == "find_and_double_click":
            return await self._find_and_double_click(args.get("target", ""))
        if action_type == "find_and_right_click":
            return await self._find_and_right_click(args.get("target", ""))
        if action_type == "scroll":
            return await self._scroll(args.get("direction", "down"), args.get("amount", 3))
        if action_type == "find_and_type":
            return await self._find_and_type(args.get("text", ""))
        if action_type == "find_element":
            return await self._find_element(args.get("target", ""))
        if action_type == "summarize_screen":
            return await self._summarize_screen()
        if action_type == "explain_screen":
            return await self._explain_screen(args.get("target", "this screen"))
        if action_type == "read_screen":
            return await self._read_screen(args.get("region", ""))
        if action_type == "analyze_screen":
            return await self._analyze_screen()
        if action_type == "query_screen":
            return await self._query_screen(args.get("question", ""))
        if action_type == "press_key":
            return await self._press_key(args.get("key", ""))
        if action_type == "hotkey":
            return await self._hotkey(args.get("keys", ""))

        return {"success": False, "error": f"Unknown action type: {action_type}"}

    async def _find_and_click(self, target: str) -> dict[str, Any]:
        if not self._last_understanding:
            return {"success": False, "error": "No screen context"}
        from vision.grounding import VisualGrounding
        grounding = VisualGrounding(confidence_threshold=self._confidence_threshold)
        grounded = grounding.ground(self._last_understanding.detected_elements)
        element = grounding.find_element(grounded, target)
        if not element:
            return {"success": False, "error": f"Could not find '{target}'", "confidence": 0.0}
        if element.confidence < self._confidence_threshold:
            msg = f"Low confidence match for '{target}': {element.confidence}"
            return {"success": False, "error": msg, "confidence": element.confidence}
        from vision.actions import mouse_click
        result = await mouse_click(element.x + element.width // 2, element.y + element.height // 2)
        result["target"] = target
        result["confidence"] = element.confidence
        return result

    async def _find_and_double_click(self, target: str) -> dict[str, Any]:
        if not self._last_understanding:
            return {"success": False, "error": "No screen context"}
        from vision.grounding import VisualGrounding
        grounding = VisualGrounding(confidence_threshold=self._confidence_threshold)
        grounded = grounding.ground(self._last_understanding.detected_elements)
        element = grounding.find_element(grounded, target)
        if not element:
            return {"success": False, "error": f"Could not find '{target}'"}
        from vision.actions import mouse_double_click
        result = await mouse_double_click(element.x + element.width // 2, element.y + element.height // 2)
        result["target"] = target
        return result

    async def _find_and_right_click(self, target: str) -> dict[str, Any]:
        if not self._last_understanding:
            return {"success": False, "error": "No screen context"}
        from vision.grounding import VisualGrounding
        grounding = VisualGrounding(confidence_threshold=self._confidence_threshold)
        grounded = grounding.ground(self._last_understanding.detected_elements)
        element = grounding.find_element(grounded, target)
        if not element:
            return {"success": False, "error": f"Could not find '{target}'"}
        from vision.actions import mouse_right_click
        result = await mouse_right_click(element.x + element.width // 2, element.y + element.height // 2)
        result["target"] = target
        return result

    async def _scroll(self, direction: str, amount: int) -> dict[str, Any]:
        from vision.actions import mouse_scroll
        try:
            x, y = 250, 250
            return await mouse_scroll(x, y, direction, amount)
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def _find_and_type(self, text: str) -> dict[str, Any]:
        from vision.actions import keyboard_type
        return await keyboard_type(text)

    async def _find_element(self, target: str) -> dict[str, Any]:
        if not self._last_understanding:
            return {"success": False, "error": "No screen context"}
        from vision.grounding import VisualGrounding
        grounding = VisualGrounding(confidence_threshold=0.0)
        grounded = grounding.ground(self._last_understanding.detected_elements)
        element = grounding.find_element(grounded, target)
        if element:
            return {"success": True, "found": True, "element": element.to_dict()}
        return {"success": True, "found": False, "target": target}

    async def _summarize_screen(self) -> dict[str, Any]:
        if not self._last_understanding:
            return {"success": False, "error": "No screen context"}
        from vision.screen_query import screen_query_engine
        return await screen_query_engine.query("what is on my screen?")

    async def _explain_screen(self, target: str) -> dict[str, Any]:
        if not self._last_understanding:
            return {"success": False, "error": "No screen context"}
        from vision.screen_query import screen_query_engine
        return await screen_query_engine.query(f"explain {target}")

    async def _read_screen(self, region: str) -> dict[str, Any]:
        if not self._last_capture_path:
            return {"success": False, "error": "No screen captured"}
        from vision.ocr import ocr_image
        result = await ocr_image(self._last_capture_path)
        text = result.get("text", "") if isinstance(result, dict) else ""
        return {"success": True, "text": text, "region": region}

    async def _analyze_screen(self) -> dict[str, Any]:
        if not self._last_capture_path:
            return {"success": False, "error": "No screen captured"}
        from vision.analyzer import analyze_image
        prompt = "Analyze this screen. Identify errors, important controls, and current state."
        result = await analyze_image(self._last_capture_path, prompt)
        return result

    async def _query_screen(self, question: str) -> dict[str, Any]:
        if not self._last_capture_path:
            return {"success": False, "error": "No screen captured"}
        from vision.question_answering import visual_qa
        return await visual_qa.answer(self._last_capture_path, question)

    async def _press_key(self, key: str) -> dict[str, Any]:
        from vision.actions import keyboard_press
        return await keyboard_press(key)

    async def _hotkey(self, keys: str) -> dict[str, Any]:
        from vision.actions import keyboard_hotkey
        return await keyboard_hotkey(keys.split("+"))


screen_intelligence = ScreenIntelligenceOrchestrator()
