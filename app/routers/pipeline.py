import asyncio
import logging
import math
from datetime import datetime, timezone
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
    reason: Optional[str] = None


@router.get("/{user_id}", response_model=PaginatedPipelineResponse)
async def get_pipeline(
    user_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str = "recommended",
    company: Optional[str] = Query(None),
    sort_by: str = Query("score", pattern="^(score|created_at)$")
) -> PaginatedPipelineResponse:
    """Get scored jobs for a user, paginated and joined with job details."""
    db = get_db()
    
    # 1. Build the matching logic for both counts and data
    match_query = {"user_id": user_id, "status": status}
    
    # Define the aggregation pipeline
    pipeline = []
    
    # Filter by user and status first
    pipeline.append({"$match": {"user_id": user_id}})
    
    # Join with jobs
    pipeline.append({
        "$lookup": {
            "from": "jobs",
            "localField": "job_id",
            "foreignField": "job_id",
            "as": "job_details"
        }
    })
    
    # Unwind job_details (should be 1-to-1)
    pipeline.append({"$unwind": "$job_details"})
    
    # Apply company filter if present
    if company:
        pipeline.append({"$match": {"job_details.company": company}})
        
    # 2. Calculate counts for all statuses (respecting company filter)
    # To do this efficiently, we'll run a separate aggregation for counts
    count_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$lookup": {
            "from": "jobs",
            "localField": "job_id",
            "foreignField": "job_id",
            "as": "job_details"
        }},
        {"$unwind": "$job_details"}
    ]
    if company:
        count_pipeline.append({"$match": {"job_details.company": company}})
    
    count_pipeline.append({"$group": {"_id": "$status", "count": {"$sum": 1}}})
    
    counts_cursor = db.pipeline.aggregate(count_pipeline)
    counts_data = await counts_cursor.to_list(length=10)
    counts_dict = {s: 0 for s in ["recommended", "saved", "applied", "ignored", "closed"]}
    for item in counts_data:
        if item["_id"] in counts_dict:
            counts_dict[item["_id"]] = item["count"]
            
    total = counts_dict.get(status, 0)
    
    # 3. Finalize data aggregation with sorting and pagination
    # Filter by the requested status
    pipeline.append({"$match": {"status": status}})
    
    # Sorting
    if sort_by == "created_at":
        pipeline.append({"$sort": {"job_details.created_at": -1, "score": -1}})
    else:
        pipeline.append({"$sort": {"score": -1, "job_details.created_at": -1}})
        
    # Pagination
    pipeline.append({"$skip": (page - 1) * limit})
    pipeline.append({"$limit": limit})
    
    # Execute
    cursor = db.pipeline.aggregate(pipeline)
    pipeline_items = await cursor.to_list(length=limit)
    
    if not pipeline_items:
        return PaginatedPipelineResponse(
            items=[],
            total=total,
            page=page,
            limit=limit,
            total_pages=math.ceil(total / limit) if total > 0 else 0,
            counts=counts_dict
        )

    # 4. Normalize results
    responses = []
    for p_item in pipeline_items:
        job = p_item["job_details"]
        
        responses.append(PipelineResponse(
            job_id=job["job_id"],
            company=job.get("company", ""),
            role=job.get("role", ""),
            description=job.get("description", ""),
            location=job.get("location", ""),
            url=job.get("url", ""),
            source=job.get("source", ""),
            created_at=job.get("created_at") or job.get("ingested_at") or datetime.now(timezone.utc),
            pipeline_score=p_item.get("score", 0.0),
            pipeline_goal_scores=p_item.get("goal_scores", {}),
            pipeline_status=p_item.get("status", "recommended"),
            pipeline_rationale=p_item.get("rationale", ""),
            pipeline_ignore_reason=p_item.get("ignore_reason"),
            pipeline_llm_verdict=p_item.get("llm_verdict"),
            pipeline_closed_at=job.get("closed_at"),
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
    
    update_data = {"status": payload.status, "updated_at": now}
    if payload.reason:
        update_data["ignore_reason"] = payload.reason

    result = await db.pipeline.update_one(
        {"user_id": user_id, "job_id": job_id},
        {"$set": update_data}
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
