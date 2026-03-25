"""Cron-based scheduler for periodic job ingestion and company discovery."""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import get_db
from app.ingestion.greenhouse import GreenhouseProvider
from app.ingestion.lever import LeverProvider
from app.ingestion.service import IngestionService

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _build_providers() -> list:
    """Construct provider instances from discovered companies in DB."""
    db = get_db()
    
    providers_gh: list[str] = []
    providers_lv: list[str] = []

    # Include companies discovered via search
    try:
        async for comp in db.companies.find({"source": "greenhouse"}, {"name": 1}):
            if comp["name"] not in providers_gh:
                providers_gh.append(comp["name"])
        async for comp in db.companies.find({"source": "lever"}, {"name": 1}):
            if comp["name"] not in providers_lv:
                providers_lv.append(comp["name"])
    except Exception:
        logger.exception("Failed to load discovered companies from DB")

    providers = []
    if providers_gh:
        providers.append(GreenhouseProvider(providers_gh))
    if providers_lv:
        providers.append(LeverProvider(providers_lv))
    return providers


async def _run_ingestion() -> None:
    """Job callback executed by the scheduler."""
    logger.info("Scheduled ingestion starting …")
    db = get_db()
    providers = await _build_providers()
    if not providers:
        logger.warning("No providers configured — skipping ingestion.")
        return
    service = IngestionService(db, providers)
    await service.run()


async def _run_discovery() -> None:
    """Discovery callback — find new companies from user goals."""
    logger.info("Scheduled discovery starting …")
    db = get_db()
    
    doc = await db.admin_settings.find_one({"_id": "settings"}, {"_id": 0})
    db_settings = doc or {}
    api_key = db_settings.get("brave_search_api_key") or settings.brave_search_api_key

    from app.discovery.service import DiscoveryService

    if api_key:
        from app.discovery.search import BraveSearchClient
        client = BraveSearchClient(api_key)
    else:
        from app.discovery.duckduckgo import DuckDuckGoClient
        client = DuckDuckGoClient()
        
    service = DiscoveryService(db, client)
    await service.run()


def start_scheduler() -> None:
    """Start the APScheduler background scheduler."""
    global _scheduler
    if _scheduler is not None:
        return

    _scheduler = AsyncIOScheduler()

    # We use .env values for the initial interval creation. 
    # The actual execution fetches the latest config.
    _scheduler.add_job(
        _run_ingestion,
        "interval",
        hours=settings.ingestion_interval_hours,
        id="job_ingestion",
        replace_existing=True,
    )

    _scheduler.add_job(
        _run_discovery,
        "interval",
        hours=settings.discovery_interval_hours,
        id="company_discovery",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info(
        "Scheduler started — ingestion every %dh, discovery every %dh",
        settings.ingestion_interval_hours,
        settings.discovery_interval_hours,
    )


def stop_scheduler() -> None:
    """Shut down the scheduler gracefully."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
