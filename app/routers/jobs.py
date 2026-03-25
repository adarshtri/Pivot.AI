"""Jobs API — list ingested jobs and trigger manual ingestion."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Query

from app.config import settings
from app.database import get_db
from app.ingestion.greenhouse import GreenhouseProvider
from app.ingestion.lever import LeverProvider
from app.ingestion.service import IngestionService
from app.models.job import JobResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])


@router.get("", response_model=list[JobResponse])
async def list_jobs(
    company: Optional[str] = Query(None, description="Filter by company"),
    source: Optional[str] = Query(None, description="Filter by source (greenhouse, lever)"),
    limit: int = Query(50, ge=1, le=500, description="Max results"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
) -> list[JobResponse]:
    """List ingested jobs with optional filters."""
    db = get_db()
    query: dict = {}
    if company:
        query["company"] = company
    if source:
        query["source"] = source

    cursor = db.jobs.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [JobResponse(**doc) for doc in docs]


@router.post("/ingest", status_code=200)
async def trigger_ingestion() -> dict:
    """Manually trigger a full ingestion run across all configured providers."""
    db = get_db()

    # Construct provider instances from discovered companies in DB
    providers_gh: list[str] = []
    providers_lv: list[str] = []

    # Also include discovered companies from DB
    async for doc in db.companies.find({"source": "greenhouse"}, {"name": 1}):
        if doc["name"] not in providers_gh:
            providers_gh.append(doc["name"])
    async for doc in db.companies.find({"source": "lever"}, {"name": 1}):
        if doc["name"] not in providers_lv:
            providers_lv.append(doc["name"])

    providers: list = []
    if providers_gh:
        providers.append(GreenhouseProvider(providers_gh))
    if providers_lv:
        providers.append(LeverProvider(providers_lv))

    if not providers:
        return {
            "status": "skipped",
            "message": "No providers configured. Set board tokens in .env or run discovery first.",
        }

    service = IngestionService(db, providers)
    summary = await service.run()
    return {"status": "completed", **summary}
