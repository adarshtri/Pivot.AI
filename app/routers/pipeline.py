import asyncio
import logging
import math
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import get_db
from app.models.pipeline import PipelineItem, PipelineResponse, PaginatedPipelineResponse
from app.scoring.engine import ScoringEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pipeline", tags=["Pipeline"])

class StatusUpdate(BaseModel):
    status: str

@router.get("/{user_id}", response_model=PaginatedPipelineResponse)
async def get_pipeline(
    user_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str = "recommended"
) -> PaginatedPipelineResponse:
    """Get scored jobs for a user, paginated and joined with job details."""
    db = get_db()
    
    # 1. Total counts for all statuses for this user
    counts_cursor = db.pipeline.aggregate([
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ])
    counts_data = await counts_cursor.to_list(length=10)
    counts_dict = {
        "recommended": 0,
        "saved": 0,
        "applied": 0,
        "ignored": 0
    }
    for item in counts_data:
        if item["_id"] in counts_dict:
            counts_dict[item["_id"]] = item["count"]
            
    total = counts_dict.get(status, 0)
    
    # 2. Fetch paginated pipeline items, sorted by score descending
    pipeline_items = await db.pipeline.find(
        {"user_id": user_id, "status": status}
    ).sort("score", -1).skip((page - 1) * limit).limit(limit).to_list(length=limit)
    
    if not pipeline_items:
        return PaginatedPipelineResponse(
            items=[],
            total=total,
            page=page,
            limit=limit,
            total_pages=math.ceil(total / limit) if total > 0 else 0,
            counts=counts_dict
        )

        
    # Map job_id -> pipeline document
    p_map = {p["job_id"]: p for p in pipeline_items}
    
    # 3. Fetch corresponding jobs
    job_ids = list(p_map.keys())
    jobs = await db.jobs.find({"job_id": {"$in": job_ids}}).to_list(length=limit)
    
    # 4. Merge and normalize
    responses = []
    # Maintain the order from pipeline_items (sorted by score)
    for p_item in pipeline_items:
        # Find the matching job
        job = next((j for j in jobs if j["job_id"] == p_item["job_id"]), None)
        if not job:
            continue
            
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
            pipeline_goal_scores=p_item.get("goal_scores", {}),
            pipeline_status=p_item.get("status", "recommended"),
            pipeline_rationale=p_item.get("rationale", ""),
            pipeline_llm_verdict=p_item.get("llm_verdict", None),
            pipeline_updated_at=p_item.get("updated_at")
        ))
        
    return PaginatedPipelineResponse(
        items=responses,
        total=total,
        page=page,
        limit=limit,
        total_pages=math.ceil(total / limit),
        counts=counts_dict
    )


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

@router.post("/{user_id}/score", status_code=202)
async def trigger_scoring(user_id: str) -> dict:
    """Trigger AI scoring engine in the background. Returns immediately."""
    db = get_db()
    engine = ScoringEngine(db)

    async def _run():
        try:
            summary = await engine.run(user_id)
            logger.info("Background scoring complete for %s: %s", user_id, summary)
        except Exception:
            logger.exception("Background scoring failed for %s", user_id)

    asyncio.create_task(_run())
    return {"status": "accepted", "message": "Scoring started in background"}

@router.post("/{user_id}/infer", status_code=202)
async def trigger_llm_inference(user_id: str) -> dict:
    """Trigger LLM inference engine in the background. Returns immediately."""
    db = get_db()
    engine = ScoringEngine(db)

    async def _run():
        try:
            summary = await engine.run_inference(user_id)
            logger.info("Background inference complete for %s: %s", user_id, summary)
        except Exception:
            logger.exception("Background inference failed for %s", user_id)

    asyncio.create_task(_run())
    return {"status": "accepted", "message": "LLM inference started in background"}
