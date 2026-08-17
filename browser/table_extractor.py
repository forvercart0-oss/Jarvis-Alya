"""Table extraction for JARVIS Phase 25.

Detects HTML tables and converts to structured data.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.browser.table_extractor")


class TableExtractor:
    async def extract_tables(self, page: Any) -> list[dict[str, Any]]:
        if page is None:
            return []
        try:
            if not hasattr(page, "evaluate"):
                return []
            tables = await page.evaluate("""
                () => Array.from(document.querySelectorAll('table')).map((table, idx) => {
                    const headers = Array.from(table.querySelectorAll('th')).map(th => (th.innerText || '').trim());
                    const rows = Array.from(table.querySelectorAll('tbody tr, tr')).map(row =>
                        Array.from(row.querySelectorAll('td, th')).map(cell => (cell.innerText || '').trim())
                    );
                    return {
                        index: idx,
                        headers: headers,
                        rows: rows,
                        row_count: rows.length,
                        column_count: headers.length || (rows[0] ? rows[0].length : 0)
                    };
                })
            """)
            return tables or []
        except Exception as exc:
            logger.debug("Table extraction failed: %s", exc)
            return []

    def table_to_markdown(self, table: dict[str, Any]) -> str:
        lines = []
        headers = table.get("headers", [])
        rows = table.get("rows", [])
        if headers:
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for row in rows:
            lines.append("| " + " | ".join(row) + " |")
        return "\n".join(lines)


table_extractor = TableExtractor()
