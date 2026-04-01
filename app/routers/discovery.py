"""Discovery and Companies API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.config import settings
from app.database import get_db
from app.auth import get_current_user
from app.discovery.search import BraveSearchClient
from app.discovery.duckduckgo import DuckDuckGoClient
from app.discovery.service import DiscoveryService
from app.models.company import CompanyResponse

router = APIRouter(prefix="/api/v1", tags=["Discovery"])


@router.post("/discovery/run", status_code=200)
async def trigger_discovery(user_id: str = Depends(get_current_user)) -> dict:
    """Manually trigger a company discovery run (authenticated)."""
    if settings.brave_search_api_key:
        client = BraveSearchClient(settings.brave_search_api_key)
    else:
        client = DuckDuckGoClient()
        
    db = get_db()
    service = DiscoveryService(db, client)
    summary = await service.run()
    return {"status": "completed", **summary}


@router.get("/companies", response_model=list[CompanyResponse])
async def list_companies(user_id: str = Depends(get_current_user)) -> list[CompanyResponse]:
    """List all discovered/stored companies with job counts and personalized matches for the current user."""
    db = get_db()
    
    # 1. Fetch companies
    cursor = db.companies.find({}, {"_id": 0}).sort("name", 1)
    companies_docs = await cursor.to_list(length=500)
    
    # 2. Pre-fetch closed job IDs for THIS specific user from the pipeline
    closed_job_ids = await db.pipeline.distinct(
        "job_id", 
        {"user_id": user_id, "status": "closed"}
    )
    
    # 3. Aggregate job counts per company
    pipeline = [
        {
            "$group": {
                "_id": "$company",
                "open": {
                    "$sum": {
                        "$cond": [
                            {"$or": [
                                {"$eq": ["$status", "CLOSED"]},
                                {"$in": ["$job_id", closed_job_ids]},
                                {"$and": [
                                    {"$ne": [{"$type": "$closed_at"}, "missing"]},
                                    {"$ne": ["$closed_at", None]}
                                ]}
                            ]},
                            0, 
                            1  
                        ]
                    }
                },
                "closed": {
                    "$sum": {
                        "$cond": [
                            {"$or": [
                                {"$eq": ["$status", "CLOSED"]},
                                {"$in": ["$job_id", closed_job_ids]},
                                {"$and": [
                                    {"$ne": [{"$type": "$closed_at"}, "missing"]},
                                    {"$ne": ["$closed_at", None]}
                                ]}
                            ]},
                            1, 
                            0  
                        ]
                    }
                }
            }
        }
    ]
    
    counts_cursor = db.jobs.aggregate(pipeline)
    counts_map = {} 
    
    async for doc in counts_cursor:
        comp_name = doc["_id"]
        if not comp_name:
            continue
            
        counts_map[comp_name] = {
            "open": doc.get("open", 0),
            "closed": doc.get("closed", 0)
        }

    # 3. Fetch personalized matches for this user
    matches_cursor = db.company_matches.find({"user_id": user_id})
    matches_list = await matches_cursor.to_list(length=1000)
    match_map = {m["company_name"]: m for m in matches_list}
    
    # 4. Merge data into results
    companies_by_name = {doc["name"]: doc for doc in companies_docs}
    all_names = set(companies_by_name.keys()) | set(counts_map.keys())
    
    results = []
    for comp_name in all_names:
        doc = companies_by_name.get(comp_name, {})
        counts = counts_map.get(comp_name, {"open": 0, "closed": 0})
        match = match_map.get(comp_name, {})
        
        results.append(CompanyResponse(
            name=comp_name,
            source=doc.get("source") or "ingested",
            domain=doc.get("domain") or "",
            stage=doc.get("stage") or "",
            size=doc.get("size") or "",
            description=doc.get("description") or "",
            priority_tag=doc.get("priority_tag") or "",
            discovered_via=doc.get("discovered_via") or ("ingestion" if comp_name in counts_map else "search"),
            open_jobs_count=counts["open"],
            closed_jobs_count=counts["closed"],
            user_match_score=match.get("score"),
            user_match_verdict=match.get("verdict"),
            user_match_rationale=match.get("rationale")
        ))
        
    results.sort(key=lambda x: (-(x.user_match_score or 0.0), -x.open_jobs_count, x.name))
        
    return results
        
    return results
