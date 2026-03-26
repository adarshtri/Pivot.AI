"""Ashby public job-board API client.

Docs: https://developers.ashbyhq.com/reference/job-board-api
Endpoint: GET https://api.ashbyhq.com/posting-api/job-board/{slug}
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from app.models.job import Job

logger = logging.getLogger(__name__)

BASE_URL = "https://api.ashbyhq.com/posting-api/job-board"


class AshbyProvider:
    """Fetches jobs from one or more Ashby board slugs."""

    def __init__(self, slugs: list[str], timeout: float = 30.0) -> None:
        self._slugs = slugs
        self._timeout = timeout

    @property
    def source_name(self) -> str:
        return "ashby"

    async def fetch_jobs(self) -> list[Job]:
        """Fetch jobs from all configured Ashby boards."""
        all_jobs: list[Job] = []

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for slug in self._slugs:
                try:
                    jobs = await self._fetch_board(client, slug)
                    all_jobs.extend(jobs)
                    logger.info("Ashby board '%s': fetched %d jobs", slug, len(jobs))
                except Exception:
                    logger.exception("Failed to fetch Ashby board '%s'", slug)

        return all_jobs

    async def _fetch_board(self, client: httpx.AsyncClient, slug: str) -> list[Job]:
        """Fetch a single board."""
        url = f"{BASE_URL}/{slug}"

        resp = await client.get(url)
        resp.raise_for_status()

        data = resp.json()
        return [self._normalize(item, slug) for item in data.get("jobs", [])]

    @staticmethod
    def _normalize(raw: dict, slug: str) -> Job:
        """Transform Ashby JSON into a normalized Job."""
        # Ashby uses 'location' as a string or object
        location_name = raw.get("location", "")
        
        # Ashby 'publishedAt' looks like ISO
        published = raw.get("publishedAt", "")
        try:
            created = datetime.fromisoformat(published.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            created = datetime.now(timezone.utc)

        return Job(
            job_id=f"as-{raw['id']}",
            company=slug, # We use the slug as the company name for now
            role=raw.get("title", ""),
            # Ashby 'descriptionHtml' is the content
            description=raw.get("descriptionHtml", ""),
            location=location_name,
            url=raw.get("jobUrl", ""),
            source="ashby",
            created_at=created,
        )
