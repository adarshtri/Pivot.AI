"""Discovery and Companies API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.database import get_db
from app.discovery.search import BraveSearchClient
from app.discovery.service import DiscoveryService
from app.models.company import CompanyResponse

router = APIRouter(prefix="/api/v1", tags=["Discovery"])


@router.post("/discovery/run", status_code=200)
async def trigger_discovery() -> dict:
    """Manually trigger a company discovery run."""
    if not settings.brave_search_api_key:
        raise HTTPException(
            status_code=400,
            detail="BRAVE_SEARCH_API_KEY not configured. Set it in .env",
        )

    db = get_db()
    client = BraveSearchClient(settings.brave_search_api_key)
    service = DiscoveryService(db, client)
    summary = await service.run()
    return {"status": "completed", **summary}


@router.get("/companies", response_model=list[CompanyResponse])
async def list_companies() -> list[CompanyResponse]:
    """List all discovered/stored companies."""
    db = get_db()
    cursor = db.companies.find({}, {"_id": 0}).sort("name", 1)
    docs = await cursor.to_list(length=500)
    return [CompanyResponse(**doc) for doc in docs]
