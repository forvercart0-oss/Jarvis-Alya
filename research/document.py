"""Document generation for Deep Research.

Generates Markdown reports and optionally PDF (if dependencies exist).
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

from research.models import ResearchJob
from research.security import sanitize_text


class ResearchDocument:
    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or os.path.expanduser("~/Documents/JARVIS-Research"))
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def build_markdown(self, job: ResearchJob) -> str:
        topic = sanitize_text(job.topic)
        lines = [
            "# Deep Research Report",
            "",
            "## Topic",
            "",
            f"{topic}",
            "",
            "## Executive Summary",
            "",
            self._summarize(job.report),
            "",
            "## Key Findings",
            "",
        ]
        for i, claim in enumerate(job.claims[:20], 1):
            lines.append(f"{i}. {sanitize_text(claim.text)} [{claim.status}]")
        lines.append("")
        lines.append("## Detailed Analysis")
        lines.append("")
        lines.append(sanitize_text(job.report or "No detailed analysis available."))
        lines.append("")
        lines.append("## Evidence")
        lines.append("")
        for i, source in enumerate(job.sources[:30], 1):
            lines.append(f"{i}. **{sanitize_text(source.title)}**")
            if source.publisher:
                lines.append(f"   - Publisher: {sanitize_text(source.publisher)}")
            lines.append(f"   - URL: {sanitize_text(source.url)}")
            if source.publication_date:
                lines.append(f"   - Date: {sanitize_text(source.publication_date)}")
            lines.append("")
        if any(c.status != "LIKELY" for c in job.claims):
            lines.append("## Conflicting Information")
            lines.append("")
            for claim in job.claims:
                if claim.status in ("DISPUTED", "UNCERTAIN"):
                    lines.append(f"- {sanitize_text(claim.text)} [{claim.status}]")
            lines.append("")
        lines.append("## Limitations")
        lines.append("")
        lines.append(
            "This report was generated automatically. Always verify critical information with primary sources."
        )
        lines.append("")
        lines.append("## Conclusion")
        lines.append("")
        lines.append(sanitize_text(job.report[:500] if job.report else "See analysis above."))
        lines.append("")
        lines.append("## Sources")
        lines.append("")
        for i, source in enumerate(job.sources[:50], 1):
            lines.append(f"{i}. {sanitize_text(source.title)}")
            if source.publisher:
                lines.append(f"   {sanitize_text(source.publisher)}")
            lines.append(f"   {sanitize_text(source.url)}")
            if source.publication_date:
                lines.append(f"   {sanitize_text(source.publication_date)}")
            lines.append("")
        return "\n".join(lines)

    def save(self, job: ResearchJob) -> str:
        filename = f"deep-research-{job.id}-{datetime.now(UTC).strftime('%Y-%m-%d')}.md"
        filepath = self.base_dir / filename
        md = self.build_markdown(job)
        filepath.write_text(md, encoding="utf-8")
        return str(filepath)

    def _summarize(self, text: str, max_chars: int = 500) -> str:
        if not text:
            return "No summary available."
        if len(text) <= max_chars:
            return text
        return text[:max_chars].rsplit(" ", 1)[0] + "..."
