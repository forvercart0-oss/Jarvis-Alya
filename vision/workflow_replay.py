"""Workflow replay for JARVIS Phase 30.

Replays recorded visual workflows with target re-detection and
verification.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.vision.workflow_replay")


class WorkflowReplayError(Exception):
    pass


class WorkflowReplayer:
    def __init__(self):
        self._stopped: bool = False

    async def replay(self, workflow: dict[str, Any], re_detect: bool = True) -> dict[str, Any]:
        self._stopped = False
        results = []

        for step in workflow.get("steps", []):
            if self._stopped:
                results.append({"step": step, "result": {"success": False, "error": "Replay stopped by user"}})
                break

            action_type = step.get("action_type", "")
            target = step.get("target", "")
            text = step.get("text_entered", "")
            coords = step.get("coordinates", {})

            if not action_type:
                continue

            try:
                if action_type in ("click", "find_and_click"):
                    from vision.grounding import VisualGrounding
                    from vision.screen_understanding import screen_understanding_engine
                    understanding = await screen_understanding_engine.understand(step.get("screenshot_path", ""))
                    grounding = VisualGrounding()
                    grounded = grounding.ground(understanding.detected_elements if understanding else [])
                    element = grounding.find_element(grounded, target) if re_detect else None
                    if not element:
                        raise WorkflowReplayError(f"Target not found: {target}")
                    from vision.actions import mouse_click
                    result = await mouse_click(element.x + element.width // 2, element.y + element.height // 2)
                    results.append({"step": step, "result": result})

                elif action_type in ("type", "find_and_type"):
                    from vision.actions import keyboard_type
                    result = await keyboard_type(text)
                    results.append({"step": step, "result": result})

                elif action_type in ("hotkey", "press_key"):
                    from vision.actions import keyboard_hotkey, keyboard_press
                    result = await keyboard_hotkey(target) if action_type == "hotkey" else await keyboard_press(target)
                    results.append({"step": step, "result": result})

                elif action_type in ("scroll",):
                    from vision.actions import mouse_scroll
                    direction = step.get("metadata", {}).get("direction", "down")
                    result = await mouse_scroll(coords.get("x", 0), coords.get("y", 0), direction)
                    results.append({"step": step, "result": result})

                else:
                    results.append({"step": step, "result": {"success": False, "error": f"Unsupported action: {action_type}"}})

            except Exception as exc:
                logger.error("Workflow replay step failed: %s", exc)
                results.append({"step": step, "result": {"success": False, "error": str(exc)}})

        success = all(r["result"].get("success", False) for r in results)
        return {"success": success, "results": results, "total_steps": len(results)}

    def stop(self) -> None:
        self._stopped = True


workflow_replayer = WorkflowReplayer()
