"""Pipeline API — manage scored jobs and user statuses."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_db
from app.models.pipeline import PipelineItem, PipelineResponse
from app.scoring.engine import ScoringEngine

router = APIRouter(prefix="/api/v1/pipeline", tags=["Pipeline"])

class StatusUpdate(BaseModel):
    status: str

@router.get("/{user_id}", response_model=list[PipelineResponse])
async def get_pipeline(user_id: str) -> list[PipelineResponse]:
    """Get all scored jobs for a user, joined with job details, sorted by score."""
    db = get_db()
    
    # 1. Fetch user's pipeline items
    pipeline_items = await db.pipeline.find({"user_id": user_id}).to_list(length=1000)
    if not pipeline_items:
        return []
        
    # Map job_id -> pipeline document
    p_map = {p["job_id"]: p for p in pipeline_items}
    
    # 2. Fetch corresponding jobs
    job_ids = list(p_map.keys())
    jobs = await db.jobs.find({"job_id": {"$in": job_ids}}).to_list(length=1000)
    
    # 3. Merge and normalize
    responses = []
    for job in jobs:
        p_item = p_map.get(job["job_id"])
        if not p_item:
            continue
            
        # Do not include the large embedding vector in the response
        responses.append(PipelineResponse(
            job_id=job["job_id"],
            company=job.get("company", ""),
            role=job.get("role", ""),
            description=job.get("description", ""),
            location=job.get("location", ""),
            url=job.get("url", ""),
            source=job.get("source", ""),
            created_at=job.get("created_at"),
            pipeline_score=p_item.get("score", 0.0),
            pipeline_status=p_item.get("status", "recommended"),
            pipeline_rationale=p_item.get("rationale", ""),
            pipeline_updated_at=p_item.get("updated_at")
        ))
        
    # Sort by score descending
    responses.sort(key=lambda r: r.pipeline_score, reverse=True)
    return responses

@router.put("/{user_id}/{job_id}/status", status_code=200)
async def update_pipeline_status(user_id: str, job_id: str, payload: StatusUpdate) -> dict:
    """Update a job's pipeline status (e.g., saved, ignored, applied)."""
    db = get_db()
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    
    result = await db.pipeline.update_one(
        {"user_id": user_id, "job_id": job_id},
        {"$set": {"status": payload.status, "updated_at": now}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Pipeline item not found")
        
    return {"status": "success", "new_status": payload.status}

@router.post("/{user_id}/score", status_code=200)
async def trigger_scoring(user_id: str) -> dict:
    """Manually trigger the AI scoring engine for a user."""
    db = get_db()
    engine = ScoringEngine(db)
    
    try:
        summary = await engine.run(user_id)
        return summary
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("Scoring engine failed")
        raise HTTPException(status_code=500, detail=str(e))
