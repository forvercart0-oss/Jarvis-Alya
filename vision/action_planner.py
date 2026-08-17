"""Visual action planner for JARVIS Phase 24.

Converts natural language screen commands into executable action sequences.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.vision.action_planner")


@dataclass
class PlannedAction:
    action_type: str
    arguments: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    confidence: float = 0.0
    expected_state: str = ""
    requires_verification: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_type": self.action_type,
            "arguments": self.arguments,
            "description": self.description,
            "confidence": self.confidence,
            "expected_state": self.expected_state,
            "requires_verification": self.requires_verification,
        }


@dataclass
class ActionPlan:
    goal: str
    actions: list[PlannedAction] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "actions": [a.to_dict() for a in self.actions],
            "confidence": self.confidence,
        }


class VisualActionPlanner:
    def __init__(self):
        self._action_patterns = [
            (r"click\s+(?:the\s+)?(.+?)(?:\s+button)?$", "click"),
            (r"double[- ]?click\s+(?:the\s+)?(.+?)(?:\s+button)?$", "double_click"),
            (r"right[- ]?click\s+(?:the\s+)?(.+?)(?:\s+button)?$", "right_click"),
            (r"scroll\s+(up|down)(?:\s+(\d+))?$", "scroll"),
            (r"type\s+['\"](.+?)['\"]$", "type"),
            (r"type\s+(.+)$", "type"),
            (r"press\s+(.+)$", "press_key"),
            (r"hotkey\s+(.+)$", "hotkey"),
            (r"find\s+(?:the\s+)?(.+)$", "find"),
            (r"search\s+(?:for\s+)?(.+)$", "find"),
            (r"open\s+(?:the\s+)?(.+)$", "open"),
            (r"close\s+(?:the\s+)?(.+)$", "close"),
            (r"read\s+(?:the\s+)?(.+)$", "read"),
            (r"explain\s+(?:this|the\s+screen|everything)$", "explain"),
            (r"explain\s+(?:the\s+)?(.+)$", "explain"),
            (r"what\s+is\s+(?:on\s+)?(?:this\s+)?(?:screen|page|window)?$", "summarize"),
            (r"what(?:'s| is)\s+(.+)$", "query"),
            (r"where\s+is\s+(?:the\s+)?(.+)$", "find"),
            (r"look\s+(?:at\s+)?(?:my\s+)?(?:screen|monitor)$", "summarize"),
            (r"analyze\s+(?:this|the\s+screen|the\s+error)$", "analyze"),
        ]

    def plan(self, text: str) -> ActionPlan:
        lower = text.lower().strip()
        actions: list[PlannedAction] = []

        for pattern, action_type in self._action_patterns:
            match = re.search(pattern, lower)
            if match:
                groups = match.groups()
                if action_type == "click":
                    actions.append(PlannedAction(
                        action_type="find_and_click",
                        arguments={"target": groups[0].strip()},
                        description=f"Find and click '{groups[0].strip()}'",
                        confidence=0.8,
                        expected_state=f"{groups[0].strip()} activated",
                    ))
                elif action_type == "double_click":
                    actions.append(PlannedAction(
                        action_type="find_and_double_click",
                        arguments={"target": groups[0].strip()},
                        description=f"Find and double-click '{groups[0].strip()}'",
                        confidence=0.7,
                    ))
                elif action_type == "right_click":
                    actions.append(PlannedAction(
                        action_type="find_and_right_click",
                        arguments={"target": groups[0].strip()},
                        description=f"Find and right-click '{groups[0].strip()}'",
                        confidence=0.7,
                    ))
                elif action_type == "scroll":
                    direction = groups[0]
                    amount = int(groups[1]) if len(groups) > 1 and groups[1] else 3
                    actions.append(PlannedAction(
                        action_type="scroll",
                        arguments={"direction": direction, "amount": amount},
                        description=f"Scroll {direction}",
                        confidence=0.9,
                    ))
                elif action_type == "type":
                    actions.append(PlannedAction(
                        action_type="find_and_type",
                        arguments={"text": groups[0].strip()},
                        description=f"Type '{groups[0].strip()}'",
                        confidence=0.8,
                    ))
                elif action_type == "press_key":
                    actions.append(PlannedAction(
                        action_type="press_key",
                        arguments={"key": groups[0].strip()},
                        description=f"Press key '{groups[0].strip()}'",
                        confidence=0.7,
                    ))
                elif action_type == "hotkey":
                    actions.append(PlannedAction(
                        action_type="hotkey",
                        arguments={"keys": groups[0].strip()},
                        description=f"Press hotkey '{groups[0].strip()}'",
                        confidence=0.7,
                    ))
                elif action_type == "find":
                    actions.append(PlannedAction(
                        action_type="find_element",
                        arguments={"target": groups[0].strip()},
                        description=f"Find '{groups[0].strip()}'",
                        confidence=0.9,
                        requires_verification=False,
                    ))
                elif action_type == "open":
                    actions.append(PlannedAction(
                        action_type="open_application",
                        arguments={"app": groups[0].strip()},
                        description=f"Open {groups[0].strip()}",
                        confidence=0.8,
                    ))
                elif action_type == "close":
                    actions.append(PlannedAction(
                        action_type="close_application",
                        arguments={"app": groups[0].strip()},
                        description=f"Close {groups[0].strip()}",
                        confidence=0.6,
                    ))
                elif action_type == "read":
                    actions.append(PlannedAction(
                        action_type="read_screen",
                        arguments={"region": groups[0].strip()},
                        description=f"Read {groups[0].strip()}",
                        confidence=0.9,
                        requires_verification=False,
                    ))
                elif action_type == "explain":
                    target = groups[0].strip() if groups[0] else "this screen"
                    actions.append(PlannedAction(
                        action_type="explain_screen",
                        arguments={"target": target},
                        description=f"Explain {target}",
                        confidence=0.9,
                        requires_verification=False,
                    ))
                elif action_type == "summarize":
                    actions.append(PlannedAction(
                        action_type="summarize_screen",
                        arguments={},
                        description="Summarize current screen",
                        confidence=0.9,
                        requires_verification=False,
                    ))
                elif action_type == "analyze":
                    actions.append(PlannedAction(
                        action_type="analyze_screen",
                        arguments={},
                        description="Analyze current screen",
                        confidence=0.9,
                        requires_verification=False,
                    ))
                elif action_type == "query":
                    actions.append(PlannedAction(
                        action_type="query_screen",
                        arguments={"question": groups[0].strip()},
                        description=f"Query: {groups[0].strip()}",
                        confidence=0.8,
                        requires_verification=False,
                    ))
                break

        if not actions:
            if any(k in lower for k in ["click", "press", "select"]):
                actions.append(PlannedAction(
                    action_type="unknown_click",
                    arguments={},
                    description="Unknown click target",
                    confidence=0.3,
                ))
            elif any(k in lower for k in ["scroll", "move down", "move up"]):
                actions.append(PlannedAction(
                    action_type="scroll",
                    arguments={"direction": "down", "amount": 3},
                    description="Scroll down",
                    confidence=0.5,
                ))
            else:
                actions.append(PlannedAction(
                    action_type="summarize_screen",
                    arguments={},
                    description="Summarize screen (fallback)",
                    confidence=0.4,
                    requires_verification=False,
                ))

        confidence = max(a.confidence for a in actions) if actions else 0.0
        return ActionPlan(goal=text, actions=actions, confidence=confidence)


visual_action_planner = VisualActionPlanner()
