"""Ingestion orchestrator — runs all providers and upserts into Plain JSON files."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.ingestion.base import JobProvider
from app.repository import FileRepository

logger = logging.getLogger(__name__)

class IngestionService:
    """Orchestrates fetching from multiple JobProviders and persists results to JSON."""

    def __init__(self, repo: FileRepository, providers: list[JobProvider]) -> None:
        self._repo = repo
        self._providers = providers

    async def run(self) -> dict[str, int]:
        """Execute a full ingestion cycle with Mark & Sweep closure detection.

        Returns a summary dict: {"total_fetched": N, "new_inserted": M, "updated": K, "closed": C}
        """
        # 1. Start a new Sync Session (using ISO format for JSON compatibility)
        sync_session_id = datetime.now(timezone.utc).isoformat()
        
        all_jobs: list[Any] = []

        for provider in self._providers:
            try:
                jobs = await provider.fetch_jobs()
                all_jobs.extend(jobs)
                logger.info("Provider '%s' returned %d jobs", provider.source_name, len(jobs))
            except Exception:
                logger.exception("Provider '%s' failed", provider.source_name)

        # 2. Deduplicate
        seen: dict[str, Any] = {job.job_id: job for job in all_jobs}

        new_count = 0
        updated_count = 0

        # 3. The Mark: Update/Insert seen jobs into FileRepository
        for job in seen.values():
            doc = job.model_dump()
            doc["status"] = "OPEN"
            
            result = await self._repo.upsert_job(doc, sync_session_id)
            if result == "inserted":
                new_count += 1
            elif result == "updated":
                updated_count += 1

        # 4. The Sweep: Mark jobs not seen in this session as CLOSED
        closed_count = await self._repo.sweep_closed_jobs(sync_session_id)

        summary = {
            "total_fetched": len(seen),
            "new_inserted": new_count,
            "updated": updated_count,
            "closed": closed_count
        }
        logger.info("Ingestion complete (File-Based): %s", summary)
        return summary
