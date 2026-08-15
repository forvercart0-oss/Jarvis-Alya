"""Known gesture definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Gesture:
    id: str
    name: str
    description: str
    default_action: str
    requires_confirmation: bool = False


GESTURES: list[Gesture] = [
    Gesture("open_palm", "Open Palm", "All five fingers extended", "stop", requires_confirmation=False),
    Gesture("thumbs_up", "Thumbs Up", "Thumb pointing up", "confirm", requires_confirmation=False),
    Gesture("thumbs_down", "Thumbs Down", "Thumb pointing down", "cancel", requires_confirmation=False),
    Gesture("point", "Point", "Index finger extended", "select", requires_confirmation=False),
    Gesture("two_fingers", "Two Fingers", "Index and middle extended", "scroll", requires_confirmation=False),
    Gesture("pinch", "Pinch", "Thumb and index close", "click", requires_confirmation=False),
    Gesture("fist", "Fist", "All fingers closed", "stop_action", requires_confirmation=False),
]


def get_gesture(gesture_id: str) -> Optional[Gesture]:
    for g in GESTURES:
        if g.id == gesture_id:
            return g
    return None
