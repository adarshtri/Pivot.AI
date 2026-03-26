"""Admin API — settings management and system operations."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.database import get_db
from app.models.admin_settings import AdminSettings, AdminSettingsResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


async def _require_admin(user_id: str) -> None:
    """Verify the user is an admin."""
    db = get_db()
    user = await db.users.find_one({"user_id": user_id}, {"is_admin": 1})
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")


async def get_admin_settings() -> AdminSettings:
    """Fetch admin settings from DB, or return defaults."""
    db = get_db()
    doc = await db.admin_settings.find_one({"_id": "settings"}, {"_id": 0})
    if doc:
        return AdminSettings(**doc)
    return AdminSettings()


@router.get("/settings", response_model=AdminSettingsResponse)
async def fetch_settings(user_id: str = "user1") -> AdminSettingsResponse:
    """Fetch current admin settings."""
    await _require_admin(user_id)
    settings = await get_admin_settings()
    return AdminSettingsResponse.from_settings(settings)


@router.put("/settings", response_model=AdminSettingsResponse)
async def update_settings(payload: AdminSettings, user_id: str = "user1") -> AdminSettingsResponse:
    """Update admin settings (stored in MongoDB)."""
    await _require_admin(user_id)
    db = get_db()

    doc = payload.model_dump()
    doc["updated_at"] = datetime.now(timezone.utc)

    # Fetch existing settings once to handle masked/empty API keys
    existing = await db.admin_settings.find_one({"_id": "settings"})

    # If brave_search_api_key is empty or masked, keep the existing one
    if not payload.brave_search_api_key or payload.brave_search_api_key == "********":
        if existing and existing.get("brave_search_api_key"):
            doc["brave_search_api_key"] = existing["brave_search_api_key"]
            
    # If llm_api_key is empty or masked, keep the existing one
    if not payload.llm_api_key or payload.llm_api_key == "********":
        if existing and existing.get("llm_api_key"):
            doc["llm_api_key"] = existing["llm_api_key"]

    await db.admin_settings.update_one(
        {"_id": "settings"},
        {"$set": doc},
        upsert=True,
    )
    logger.info("Admin settings updated")
    updated = await get_admin_settings()
    return AdminSettingsResponse.from_settings(updated)


@router.post("/discovery/run")
async def admin_trigger_discovery(user_id: str = "user1") -> dict:
    """Trigger company discovery (admin only)."""
    await _require_admin(user_id)

    settings = await get_admin_settings()
    api_key = settings.brave_search_api_key
    if not api_key:
        # Fallback to .env
        from app.config import settings as env_settings
        api_key = env_settings.brave_search_api_key

    from app.discovery.service import DiscoveryService

    db = get_db()
    
    if api_key:
        from app.discovery.search import BraveSearchClient
        client = BraveSearchClient(api_key)
    else:
        from app.discovery.duckduckgo import DuckDuckGoClient
        client = DuckDuckGoClient()
        
    service = DiscoveryService(db, client)
    summary = await service.run()
    return {"status": "completed", **summary}


@router.post("/ingestion/run")
async def admin_trigger_ingestion(user_id: str = "user1") -> dict:
    """Trigger job ingestion (admin only)."""
    await _require_admin(user_id)

    from app.config import settings as env_settings
    from app.ingestion.greenhouse import GreenhouseProvider
    from app.ingestion.lever import LeverProvider
    from app.ingestion.ashby import AshbyProvider
    from app.ingestion.service import IngestionService

    db = get_db()
    
    gh_tokens = []
    lv_slugs = []
    as_slugs = []

    # Only include discovered companies
    async for doc in db.companies.find({"source": "greenhouse"}, {"name": 1}):
        if doc["name"] not in gh_tokens:
            gh_tokens.append(doc["name"])
    async for doc in db.companies.find({"source": "lever"}, {"name": 1}):
        if doc["name"] not in lv_slugs:
            lv_slugs.append(doc["name"])
    async for doc in db.companies.find({"source": "ashby"}, {"name": 1}):
        if doc["name"] not in as_slugs:
            as_slugs.append(doc["name"])

    providers = []
    if gh_tokens:
        providers.append(GreenhouseProvider(gh_tokens))
    if lv_slugs:
        providers.append(LeverProvider(lv_slugs))
    if as_slugs:
        providers.append(AshbyProvider(as_slugs))

    if not providers:
        return {"status": "skipped", "message": "No providers configured"}

    service = IngestionService(db, providers)
    summary = await service.run()
    return {"status": "completed", **summary}

