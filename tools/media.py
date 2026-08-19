"""Media generation tools."""

from __future__ import annotations


from tools.registry import ToolResult
from generation.image.manager import ImageGenerationManager
from generation.video.manager import VideoGenerationManager


class GenerateImageTool:
    name = "generate_image"
    description = "Generate an image from a text prompt."
    parameters = {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "The image description"},
            "provider": {"type": "string", "description": "Preferred provider (auto, puter, pixazo, gemini)"},
            "width": {"type": "integer", "description": "Image width"},
            "height": {"type": "integer", "description": "Image height"},
            "negative_prompt": {"type": "string", "description": "Negative prompt"},
        },
        "required": ["prompt"],
    }

    def __init__(self):
        self._image_mgr = ImageGenerationManager()

    async def execute(self, prompt: str, provider: str = "auto", width: int = 1024, height: int = 1024, negative_prompt: str = "", **kwargs) -> ToolResult:
        if not self._image_mgr.is_available():
            return ToolResult(success=False, error="Image generation is not available. Configure an image provider in Settings.")
        result = await self._image_mgr.generate(prompt, provider=None if provider == "auto" else provider, width=width, height=height, negative_prompt=negative_prompt)
        if result.get("success"):
            urls = result.get("urls", [])
            if urls:
                return ToolResult(success=True, result={"url": urls[0], "provider": result.get("provider"), "all_urls": urls})
            return ToolResult(success=True, result={"provider": result.get("provider"), "text": result.get("text", "Image generated.")})
        return ToolResult(success=False, error=result.get("error", "Image generation failed."))


class GenerateVideoTool:
    name = "generate_video"
    description = "Generate a video from a text prompt."
    parameters = {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "The video description"},
            "provider": {"type": "string", "description": "Preferred provider (auto, fal, magic_hour)"},
            "duration": {"type": "integer", "description": "Duration in seconds"},
            "resolution": {"type": "string", "description": "Resolution (720p, 1080p)"},
            "aspect_ratio": {"type": "string", "description": "Aspect ratio (16:9, 9:16, 1:1)"},
        },
        "required": ["prompt"],
    }

    def __init__(self):
        self._video_mgr = VideoGenerationManager()

    async def execute(self, prompt: str, provider: str = "auto", duration: int = 5, resolution: str = "720p", aspect_ratio: str = "16:9", **kwargs) -> ToolResult:
        if not self._video_mgr.is_available():
            return ToolResult(success=False, error="Video generation is not available. Configure a video provider in Settings.")
        result = await self._video_mgr.generate(prompt, provider=None if provider == "auto" else provider, duration=duration, resolution=resolution, aspect_ratio=aspect_ratio)
        if result.get("success"):
            return ToolResult(success=True, result={"job_id": result.get("job_id"), "provider": result.get("provider"), "status": "queued"})
        return ToolResult(success=False, error=result.get("error", "Video generation failed."))
