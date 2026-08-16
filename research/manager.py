"""Research job manager for Deep Research.

Manages concurrent research jobs, tracks status, and coordinates the pipeline.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from research.document import ResearchDocument
from research.extractor import SourceExtractor
from research.models import ResearchJob, ResearchStatus
from research.pipeline import ResearchPipeline
from research.searcher import ResearchSearcher

logger = logging.getLogger("jarvis.research.manager")


class ResearchManager:
    def __init__(
        self,
        ai_provider: Any | None = None,
        max_sources: int = 20,
        on_event: Callable[[str, dict[str, Any]], None] | None = None,
    ):
        self.ai_provider = ai_provider
        self.max_sources = max_sources
        self.on_event = on_event
        self._jobs: dict[str, ResearchJob] = {}
        self._tasks: dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()

    async def start_research(self, topic: str) -> ResearchJob:
        job = ResearchJob.create(topic)
        async with self._lock:
            self._jobs[job.id] = job
        task = asyncio.create_task(self._run(job))
        self._tasks[job.id] = task
        return job

    async def cancel_research(self, job_id: str) -> bool:
        async with self._lock:
            job = self._jobs.get(job_id)
            task = self._tasks.get(job_id)
        if not job or not task:
            return False
        if job.status == ResearchStatus.RUNNING:
            task.cancel()
            job.status = ResearchStatus.CANCELLED
            job.phase = job.phase
            await self._emit("research_cancelled", {"job_id": job.id})
            return True
        return False

    async def get_job(self, job_id: str) -> ResearchJob | None:
        async with self._lock:
            return self._jobs.get(job_id)

    async def list_jobs(self) -> list[ResearchJob]:
        async with self._lock:
            return list(self._jobs.values())

    async def _run(self, job: ResearchJob):
        searcher = ResearchSearcher(max_sources=self.max_sources)
        extractor = SourceExtractor()
        document_writer = ResearchDocument()
        pipeline = ResearchPipeline(
            searcher=searcher,
            extractor=extractor,
            document_writer=document_writer,
            ai_provider=self.ai_provider,
            max_sources=self.max_sources,
            on_event=self._emit_safe,
        )
        try:
            result = await pipeline.run(job)
            async with self._lock:
                self._jobs[job.id] = result
        except asyncio.CancelledError:
            async with self._lock:
                self._jobs[job.id] = job
            raise

    async def _emit(self, event: str, data: dict[str, Any]):
        if self.on_event:
            try:
                await self.on_event(event, data)
            except Exception as exc:
                logger.warning("Emit failed: %s", exc)

    async def _emit_safe(self, event: str, data: dict[str, Any]):
        await self._emit(event, data)
