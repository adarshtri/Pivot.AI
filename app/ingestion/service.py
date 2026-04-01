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
        """Execute a full ingestion cycle with Mark & Sweep closure detection.

        Returns a summary dict: {"total_fetched": N, "new_inserted": M, "updated": K, "closed": C}
        """
        # 1. Start a new Sync Session
        sync_session_id = datetime.now(timezone.utc)
        
        # 2. Legacy Migration: Give existing OPEN (or missing status) jobs the current session ID.
        # This saves them from the sweep in THIS first run.
        await self._db.jobs.update_many(
            {
                "$or": [
                    {"status": "OPEN"},
                    {"status": {"$exists": False}}
                ],
                "last_sync_id": {"$exists": False}
            },
            {"$set": {"status": "OPEN", "last_sync_id": sync_session_id}}
        )

        all_jobs: list[Job] = []

        for provider in self._providers:
            try:
                jobs = await provider.fetch_jobs()
                all_jobs.extend(jobs)
                logger.info("Provider '%s' returned %d jobs", provider.source_name, len(jobs))
            except Exception:
                logger.exception("Provider '%s' failed", provider.source_name)

        # Deduplicate
        seen: dict[str, Job] = {job.job_id: job for job in all_jobs}

        new_count = 0
        updated_count = 0

        # 3. The Mark: Update/Insert seen jobs with current session ID
        for job in seen.values():
            result = await self._upsert_job(job, sync_session_id)
            if result == "inserted":
                new_count += 1
            elif result == "updated":
                updated_count += 1

        # 4. The Sweep: Mark jobs that were NOT seen in this session as CLOSED
        # We only sweep jobs that are OPEN and have a last_sync_id < current session
        cursor = self._db.jobs.find(
            {"status": "OPEN", "last_sync_id": {"$lt": sync_session_id}},
            {"job_id": 1}
        )
        closed_job_ids = [doc["job_id"] for doc in await cursor.to_list(length=1000)]
        
        if closed_job_ids:
            # Update jobs collection
            await self._db.jobs.update_many(
                {"job_id": {"$in": closed_job_ids}},
                {"$set": {"status": "CLOSED", "closed_at": sync_session_id}}
            )
            # Update pipeline collection for ALL users who might have these jobs
            # This ensures they move to the 'closed' tab in the UI
            await self._db.pipeline.update_many(
                {"job_id": {"$in": closed_job_ids}},
                {"$set": {"status": "closed", "updated_at": sync_session_id}}
            )
            closed_count = len(closed_job_ids)
        else:
            closed_count = 0

        summary = {
            "total_fetched": len(seen),
            "new_inserted": new_count,
            "updated": updated_count,
            "closed": closed_count
        }
        logger.info("Ingestion complete: %s", summary)
        return summary

    async def _upsert_job(self, job: Job, sync_session_id: datetime) -> str:
        """Insert or update a job. Returns 'inserted', 'updated', or 'unchanged'."""
        doc = job.model_dump()
        doc["ingested_at"] = datetime.now(timezone.utc)
        doc["last_sync_id"] = sync_session_id
        doc["status"] = "OPEN" # If we see it, it is definitely open

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
