import subprocess
from tools.registry import ToolResult


class OpenBrowserTool:
    name = "open_browser"
    description = "Open a URL in the default browser."
    parameters = {
        "type": "object",
        "properties": {"url": {"type": "string"}},
        "required": ["url"],
    }

    async def execute(self, url: str, **kwargs) -> ToolResult:
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        try:
            subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return ToolResult(success=True, result={"url": url})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))
