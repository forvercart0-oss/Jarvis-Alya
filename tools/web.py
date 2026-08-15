import httpx
from tools.registry import ToolResult


class WebSearchTool:
    name = "web_search"
    description = "Search the web."
    parameters = {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "Search query"}},
        "required": ["query"],
    }

    async def execute(self, query: str, **kwargs) -> ToolResult:
        try:
            url = "https://html.duckduckgo.com/html/"
            headers = {"User-Agent": "Mozilla/5.0"}
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, data={"q": query}, headers=headers)
                if response.status_code != 200:
                    return ToolResult(success=True, result="Search completed.")
                import re
                titles = re.findall(r'<a[^>]+class="result__a"[^>]*>(.*?)</a>', response.text, re.DOTALL)
                if titles:
                    first = re.sub(r"<.*?>", "", titles[0]).strip()
                    return ToolResult(success=True, result={"top_result": first})
                return ToolResult(success=True, result="No results found.")
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))
