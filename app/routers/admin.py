"""Admin API — settings management and system operations."""

from __future__ import annotations

import logging
import httpx
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

    update_fields = payload.model_dump(exclude_unset=True)
    update_fields["updated_at"] = datetime.now(timezone.utc)

    # Fetch existing settings once to handle masked/empty API keys
    existing = await db.admin_settings.find_one({"_id": "settings"})

    # If brave_search_api_key is empty or masked, keep the existing one
    if not payload.brave_search_api_key or payload.brave_search_api_key == "********":
        if existing and existing.get("brave_search_api_key"):
            update_fields["brave_search_api_key"] = existing["brave_search_api_key"]
            
    # If llm_api_key is empty or masked, keep the existing one
    if not payload.llm_api_key or payload.llm_api_key == "********":
        if existing and existing.get("llm_api_key"):
            update_fields["llm_api_key"] = existing["llm_api_key"]

    await db.admin_settings.update_one(
        {"_id": "settings"},
        {"$set": update_fields},
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


@router.post("/telegram/sync-webhooks")
async def admin_sync_telegram_webhooks(user_id: str = "user1") -> dict:
    """Sync the base webhook URL to all configured Telegram bot tokens."""
    await _require_admin(user_id)
    db = get_db()
    settings = await get_admin_settings()
    
    base_url = settings.telegram_webhook_base_url
    if not base_url:
        raise HTTPException(status_code=400, detail="Telegram Webhook Base URL not configured in Admin Settings")

    # Normalize base_url (remove whitespace and trailing slash)
    base_url = base_url.strip().rstrip("/")

    
    logger.info(f"Syncing Telegram webhooks with base_url: {base_url}")
    
    success_count = 0
    errors = []
    
    # Find all users with a telegram token (not null and not empty)
    cursor = db.users.find({"telegram_token": {"$nin": [None, ""]}}, {"telegram_token": 1, "user_id": 1})
    async for user in cursor:
        token = user["telegram_token"]

        # webhook_url = {base_url}/api/v1/telegram/webhook/{token}
        webhook_url = f"{base_url}/api/v1/telegram/webhook/{token}"
        api_url = f"https://api.telegram.org/bot{token}/setWebhook?url={webhook_url}"
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(api_url)
                resp.raise_for_status()
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to sync webhook for user {user['user_id']}: {e}")
                errors.append({"user_id": user["user_id"], "error": str(e)})

    return {
        "status": "completed",
        "synced_count": success_count,
        "errors": errors
    }


@router.post("/telegram/test-alert")
async def admin_test_telegram_message(target_user_id: str, user_id: str = "user1") -> dict:
    """Send a manual test notification to a specific user's Telegram bot."""
    await _require_admin(user_id)
    db = get_db()
    
    user = await db.users.find_one({"user_id": target_user_id})
    if not user or not user.get("telegram_token") or not user.get("telegram_chat_id"):
        raise HTTPException(status_code=400, detail="User does not have Telegram configured or hasn't messaged /start")

    from app.telegram_utils import send_telegram_message
    
    success = await send_telegram_message(
        user["telegram_token"], 
        user["telegram_chat_id"], 
        "<b>🔔 Pivot.AI Test Notification</b>\n\nYour Telegram integration is working correctly!"
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send Telegram message")
        
    return {"status": "success", "message": f"Test alert sent to {target_user_id}"}


@router.post("/scoring/companies/run")
async def admin_run_company_scoring(force: bool = False, user_id: str = "user1") -> dict:
    """Run personalized company scoring for a user (admin only)."""
    await _require_admin(user_id)
    db = get_db()
    from app.scoring.company_engine import CompanyScoringEngine
    engine = CompanyScoringEngine(db)
    
    summary = await engine.score_all_for_user(user_id, force=force)
    return summary


from fastapi import BackgroundTasks

@router.post("/discovery/companies/enrich")
async def admin_run_company_enrichment(
    background_tasks: BackgroundTasks,
    force: bool = False, 
    user_id: str = "user1"
) -> dict:
    """Retroactively enrich existing companies with AI metadata (admin only)."""
    await _require_admin(user_id)
    db = get_db()
    from app.discovery.search import BraveSearchClient
    from app.discovery.service import DiscoveryService
    from app.config import settings
    
    # We don't need a real search client for enrichment, but the service needs one
    client = BraveSearchClient(settings.brave_search_api_key or "dummy")
    service = DiscoveryService(db, client)
    
    # Run enrichment in background to avoid blocking the API
    background_tasks.add_task(service.run_enrichment, force=force)
    
    return {"status": "started", "message": "Company enrichment started in background"}



