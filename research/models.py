"""Data models for Deep Research."""

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


class ResearchStatus(enum.StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ResearchPhase(enum.StrEnum):
    IDLE = "idle"
    UNDERSTANDING_QUERY = "understanding_query"
    SEARCHING_SOURCES = "searching_sources"
    COLLECTING_EVIDENCE = "collecting_evidence"
    CROSS_CHECKING = "cross_checking"
    ANALYZING_SOURCES = "analyzing_sources"
    WRITING_REPORT = "writing_report"
    SAVING_DOCUMENT = "saving_document"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ResearchSource:
    title: str
    url: str
    publisher: str = ""
    publication_date: str = ""
    retrieval_date: str = ""
    relevance: float = 0.0
    source_type: str = "web"
    content: str = ""
    claims: list[str] = field(default_factory=list)


@dataclass
class ResearchClaim:
    text: str
    sources: list[str] = field(default_factory=list)
    status: str = "LIKELY"
    confidence: float = 0.0


@dataclass
class ResearchJob:
    id: str
    topic: str
    status: ResearchStatus
    phase: ResearchPhase
    started_at: float
    completed_at: float | None = None
    sources_found: int = 0
    sources_processed: int = 0
    claims_checked: int = 0
    document_path: str = ""
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    sources: list[ResearchSource] = field(default_factory=list)
    claims: list[ResearchClaim] = field(default_factory=list)
    report: str = ""

    @staticmethod
    def create(topic: str) -> ResearchJob:
        return ResearchJob(
            id=str(uuid.uuid4())[:8],
            topic=topic,
            status=ResearchStatus.QUEUED,
            phase=ResearchPhase.IDLE,
            started_at=time.time(),
        )
