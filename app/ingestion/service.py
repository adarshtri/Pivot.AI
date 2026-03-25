"""Ingestion orchestrator — runs all providers and upserts into MongoDB."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ingestion.base import JobProvider
from app.models.job import Job

logger = logging.getLogger(__name__)


class IngestionService:
    """Orchestrates fetching from multiple JobProviders and persists results."""

    def __init__(self, db: AsyncIOMotorDatabase, providers: list[JobProvider]) -> None:
        self._db = db
        self._providers = providers

    async def run(self) -> dict[str, int]:
        """Execute a full ingestion cycle.

        Returns a summary dict: {"total_fetched": N, "new_inserted": M, "updated": K}
        """
        all_jobs: list[Job] = []

        for provider in self._providers:
            try:
                jobs = await provider.fetch_jobs()
                all_jobs.extend(jobs)
                logger.info(
                    "Provider '%s' returned %d jobs",
                    provider.source_name,
                    len(jobs),
                )
            except Exception:
                logger.exception("Provider '%s' failed", provider.source_name)

        # Deduplicate by job_id (last wins if dupes within batch)
        seen: dict[str, Job] = {}
        for job in all_jobs:
            seen[job.job_id] = job

        new_count = 0
        updated_count = 0

        for job in seen.values():
            result = await self._upsert_job(job)
            if result == "inserted":
                new_count += 1
            elif result == "updated":
                updated_count += 1

        summary = {
            "total_fetched": len(seen),
            "new_inserted": new_count,
            "updated": updated_count,
        }
        logger.info("Ingestion complete: %s", summary)
        return summary

    async def _upsert_job(self, job: Job) -> str:
        """Insert or update a job. Returns 'inserted', 'updated', or 'unchanged'."""
        doc = job.model_dump()
        doc["_ingested_at"] = datetime.now(timezone.utc)

        result = await self._db.jobs.update_one(
            {"job_id": job.job_id},
            {"$set": doc},
            upsert=True,
        )

        if result.upserted_id:
            return "inserted"
        elif result.modified_count > 0:
            return "updated"
        return "unchanged"
