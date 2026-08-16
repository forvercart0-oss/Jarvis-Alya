from fastapi import APIRouter

from safety.activity import get_activity_logger

router = APIRouter()


@router.get("/activity")
async def get_activity(limit: int = 100):
    """Return recent safe activity log entries (secrets already masked)."""
    limit = max(1, min(limit, 500))
    return {"entries": get_activity_logger().recent(limit)}
