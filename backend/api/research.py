"""REST API endpoints for Deep Research."""


from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ResearchStartRequest(BaseModel):
    topic: str


class ResearchSettingsUpdate(BaseModel):
    max_sources: int | None = None
    research_depth: str | None = None
    document_format: str | None = None


@router.post("/research/start")
async def start_research(request: ResearchStartRequest):
    from backend.main import research_manager
    job = await research_manager.start_research(request.topic)
    return {
        "job_id": job.id,
        "topic": job.topic,
        "status": job.status.value,
        "phase": job.phase.value,
    }


@router.post("/research/{job_id}/cancel")
async def cancel_research(job_id: str):
    from backend.main import research_manager
    ok = await research_manager.cancel_research(job_id)
    return {"cancelled": ok}


@router.get("/research/jobs")
async def list_research_jobs():
    from backend.main import research_manager
    jobs = await research_manager.list_jobs()
    return {
        "jobs": [
            {
                "id": j.id,
                "topic": j.topic,
                "status": j.status.value,
                "phase": j.phase.value,
                "started_at": j.started_at,
                "completed_at": j.completed_at,
                "sources_found": j.sources_found,
                "sources_processed": j.sources_processed,
                "claims_checked": j.claims_checked,
                "document_path": j.document_path,
                "error": j.error,
            }
            for j in jobs
        ]
    }


@router.get("/research/{job_id}")
async def get_research_job(job_id: str):
    from backend.main import research_manager
    job = await research_manager.get_job(job_id)
    if not job:
        return {"error": "not_found"}
    return {
        "id": job.id,
        "topic": job.topic,
        "status": job.status.value,
        "phase": job.phase.value,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "sources_found": job.sources_found,
        "sources_processed": job.sources_processed,
        "claims_checked": job.claims_checked,
        "document_path": job.document_path,
        "error": job.error,
        "sources": [
            {
                "title": s.title,
                "url": s.url,
                "publisher": s.publisher,
                "publication_date": s.publication_date,
                "source_type": s.source_type,
            }
            for s in job.sources[:20]
        ],
        "report": job.report[:5000] if job.report else "",
    }


@router.get("/research/settings")
async def get_research_settings():
    from config.settings import get_settings
    s = get_settings()
    return {
        "max_sources": getattr(s, "research_max_sources", 20),
        "research_depth": getattr(s, "research_depth", "deep"),
        "document_format": getattr(s, "research_document_format", "markdown"),
    }


@router.put("/research/settings")
async def update_research_settings(update: ResearchSettingsUpdate):
    from backend.main import memory_manager
    from config.settings import get_settings
    s = get_settings()
    updates = update.model_dump(exclude_none=True)
    for key, value in updates.items():
        if not hasattr(s, key):
            memory_manager.store.set_setting(f"research_{key}", str(value))
        else:
            setattr(s, key, value)
    s.persist()
    return await get_research_settings()
