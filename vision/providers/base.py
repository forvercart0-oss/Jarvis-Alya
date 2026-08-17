"""Vision provider base class for JARVIS Phase 4.

Defines the abstraction for vision backends (local or cloud).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class VisionResult:
    success: bool
    description: str = ""
    elements: list[dict[str, Any]] = field(default_factory=list)
    text: str = ""
    error: str = ""
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class VisionProvider(ABC):
    """Abstract vision provider."""

    name: str = "base"

    @abstractmethod
    async def analyze_image(self, image_path: str, prompt: str = "") -> VisionResult:
        """Analyze an image and return a description or answer."""
        raise NotImplementedError

    @abstractmethod
    async def detect_elements(self, image_path: str) -> VisionResult:
        """Detect UI elements in an image."""
        raise NotImplementedError

    @abstractmethod
    async def describe_screen(self, image_path: str) -> VisionResult:
        """Provide a high-level description of the screen."""
        raise NotImplementedError

    @abstractmethod
    async def find_target(self, image_path: str, target: str) -> VisionResult:
        """Find a specific UI target by name/description."""
        raise NotImplementedError

    @abstractmethod
    async def understand_ui(self, image_path: str) -> VisionResult:
        """Understand the UI layout and elements."""

    @abstractmethod
    async def answer_visual_question(self, image_path: str, question: str) -> VisionResult:
        """Answer a natural language question about the image."""

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Return provider health status."""
        raise NotImplementedError
