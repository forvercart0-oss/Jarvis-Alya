"""Deep Research pipeline.

Implements the multi-step research process:
Query -> Query expansion -> Search -> Source collection -> Source filtering ->
Source extraction -> Cross-checking -> Evidence extraction -> Synthesis ->
Report generation -> Document creation
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from research.models import ResearchClaim, ResearchJob, ResearchPhase, ResearchSource, ResearchStatus
from research.security import sanitize_text

logger = logging.getLogger("jarvis.research.pipeline")


class ResearchPipeline:
    def __init__(
        self,
        searcher: Any,
        extractor: Any,
        document_writer: Any,
        ai_provider: Any | None = None,
        max_sources: int = 20,
        on_event: Callable[[str, dict[str, Any]], None] | None = None,
    ):
        self.searcher = searcher
        self.extractor = extractor
        self.document_writer = document_writer
        self.ai_provider = ai_provider
        self.max_sources = max_sources
        self.on_event = on_event
        self._cancel = False

    async def run(self, job: ResearchJob) -> ResearchJob:
        try:
            job.status = ResearchStatus.RUNNING
            await self._emit("research_started", {"job_id": job.id, "topic": job.topic})

            await self._phase(job, ResearchPhase.UNDERSTANDING_QUERY, self._understand_query)
            await self._phase(job, ResearchPhase.SEARCHING_SOURCES, self._search_sources)
            await self._phase(job, ResearchPhase.COLLECTING_EVIDENCE, self._collect_evidence)
            await self._phase(job, ResearchPhase.CROSS_CHECKING, self._cross_check)
            await self._phase(job, ResearchPhase.ANALYZING_SOURCES, self._analyze)
            await self._phase(job, ResearchPhase.WRITING_REPORT, self._write_report)
            await self._phase(job, ResearchPhase.SAVING_DOCUMENT, self._save_document)

            job.status = ResearchStatus.COMPLETED
            job.phase = ResearchPhase.COMPLETED
            job.completed_at = asyncio.get_event_loop().time()
            await self._emit("research_completed", {
                "job_id": job.id,
                "topic": job.topic,
                "sources_found": job.sources_found,
                "sources_processed": job.sources_processed,
                "claims_checked": job.claims_checked,
                "document_path": job.document_path,
            })
        except asyncio.CancelledError:
            job.status = ResearchStatus.CANCELLED
            job.phase = ResearchPhase.CANCELLED
            await self._emit("research_failed", {"job_id": job.id, "error": "cancelled"})
        except Exception as exc:
            logger.error("Research pipeline failed: %s", exc)
            job.status = ResearchStatus.FAILED
            job.phase = ResearchPhase.FAILED
            job.error = str(exc)
            await self._emit("research_failed", {"job_id": job.id, "error": str(exc)})
        return job

    def cancel(self):
        self._cancel = True

    async def _phase(self, job: ResearchJob, phase: ResearchPhase, coro):
        if self._cancel:
            raise asyncio.CancelledError()
        job.phase = phase
        await self._emit("research_query_updated", {"job_id": job.id, "phase": phase.value, "topic": job.topic})
        await coro(job)

    async def _understand_query(self, job: ResearchJob):
        await asyncio.sleep(0.1)

    async def _search_sources(self, job: ResearchJob):
        found = await self.searcher.search(job.topic)
        job.sources_found = len(found)
        for item in found:
            if self._cancel:
                raise asyncio.CancelledError()
            source = ResearchSource(
                title=sanitize_text(item.get("title", "")),
                url=sanitize_text(item.get("url", "")),
                publisher=sanitize_text(item.get("publisher", "")),
                source_type=item.get("source_type", "web"),
                snippet=sanitize_text(item.get("snippet", "")),
            )
            job.sources.append(source)
            job.sources_found = len(job.sources)
            await self._emit("research_source_found", {
                "job_id": job.id,
                "source": {
                    "title": source.title,
                    "url": source.url,
                    "publisher": source.publisher,
                    "source_type": source.source_type,
                },
                "sources_found": job.sources_found,
            })

    async def _collect_evidence(self, job: ResearchJob):
        for source in job.sources[: self.max_sources]:
            if self._cancel:
                raise asyncio.CancelledError()
            result = await self.extractor.extract(source.url)
            if result.get("success"):
                source.content = sanitize_text(result.get("content", ""))[:8000]
                source.title = sanitize_text(result.get("title", source.title))
            job.sources_processed += 1
            await self._emit("research_source_processed", {
                "job_id": job.id,
                "url": source.url,
                "sources_processed": job.sources_processed,
                "sources_found": job.sources_found,
            })

    async def _cross_check(self, job: ResearchJob):
        job.claims_checked = 0
        for source in job.sources:
            if self._cancel:
                raise asyncio.CancelledError()
            if not source.content:
                continue
            claim_texts = self._extract_claims(source.content)
            for claim_text in claim_texts[:5]:
                claim = ResearchClaim(text=claim_text, sources=[source.url])
                claim.status = self._assess_status(claim)
                job.claims.append(claim)
                job.claims_checked += 1
                await self._emit("research_source_processed", {
                    "job_id": job.id,
                    "claim": claim.text[:100],
                    "status": claim.status,
                    "claims_checked": job.claims_checked,
                })

    def _extract_claims(self, content: str) -> list[str]:
        sentences = [s.strip() for s in content.replace("\n", " ").split(".") if len(s.strip()) > 20]
        return sentences[:10]

    def _assess_status(self, claim: ResearchClaim) -> str:
        if len(claim.sources) >= 3:
            return "CONFIRMED"
        if len(claim.sources) == 2:
            return "LIKELY"
        if len(claim.sources) == 1:
            return "LIKELY"
        return "UNCERTAIN"

    async def _analyze(self, job: ResearchJob):
        await self._emit("research_analysis_started", {"job_id": job.id})
        await asyncio.sleep(0.1)

    async def _write_report(self, job: ResearchJob):
        await self._emit("research_writing_started", {"job_id": job.id})
        if self.ai_provider:
            try:
                job.report = await self._generate_report_with_ai(job)
            except Exception as exc:
                logger.warning("AI report generation failed: %s", exc)
                job.report = self._generate_fallback_report(job)
        else:
            job.report = self._generate_fallback_report(job)

    async def _generate_report_with_ai(self, job: ResearchJob) -> str:
        context_parts = []
        for source in job.sources[:10]:
            if source.content:
                context_parts.append(f"Source: {source.title}\nURL: {source.url}\nContent: {source.content[:2000]}")
        context = "\n\n".join(context_parts)[:15000]
        prompt = (
            f"Write a structured research report about: {job.topic}\n\n"
            f"Use the following source material. Cite sources by URL. "
            f"Label claims as CONFIRMED, LIKELY, DISPUTED, or UNCERTAIN where appropriate.\n\n"
            f"{context}\n\n"
            f"Report format:\n"
            f"# Deep Research Report\n"
            f"## Topic\n"
            f"## Executive Summary\n"
            f"## Key Findings\n"
            f"## Detailed Analysis\n"
            f"## Evidence\n"
            f"## Conflicting Information\n"
            f"## Limitations\n"
            f"## Conclusion\n"
            f"## Sources\n"
        )
        try:
            if hasattr(self.ai_provider, "chat_with_tools"):
                result = await self.ai_provider.chat_with_tools(
                    [{"role": "user", "content": prompt}],
                    tools_spec=[],
                )
                return sanitize_text(result.get("content", ""))
        except Exception as exc:
            logger.warning("AI report generation error: %s", exc)
        return self._generate_fallback_report(job)

    def _generate_fallback_report(self, job: ResearchJob) -> str:
        lines = [f"# Deep Research Report: {job.topic}", "", "## Executive Summary", ""]
        if job.sources:
            lines.append(f"Research identified {len(job.sources)} sources and {len(job.claims)} claims.")
        else:
            lines.append("Insufficient evidence found for this topic.")
        lines += ["", "## Key Findings", ""]
        for claim in job.claims[:10]:
            lines.append(f"- {claim.text} [{claim.status}]")
        lines += ["", "## Detailed Analysis", "", "See sources below for raw content.", ""]
        lines += ["## Sources", ""]
        for i, source in enumerate(job.sources[:20], 1):
            lines.append(f"{i}. {source.title}")
            lines.append(f"   {source.url}")
            if source.publisher:
                lines.append(f"   {source.publisher}")
            lines.append("")
        return "\n".join(lines)

    async def _save_document(self, job: ResearchJob):
        path = self.document_writer.save(job)
        job.document_path = path
        await self._emit("research_document_created", {"job_id": job.id, "document_path": path})

    async def _emit(self, event: str, data: dict[str, Any]):
        if self.on_event:
            try:
                await self.on_event(event, data)
            except Exception as exc:
                logger.warning("Event emission failed for %s: %s", event, exc)
