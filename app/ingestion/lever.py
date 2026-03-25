"""Lever public postings API client.

Docs: https://github.com/lever/postings-api
Endpoint: GET https://api.lever.co/v0/postings/{company}?mode=json
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from app.models.job import Job

logger = logging.getLogger(__name__)

BASE_URL = "https://api.lever.co/v0/postings"


class LeverProvider:
    """Fetches jobs from one or more Lever company slugs."""

    def __init__(self, company_slugs: list[str], timeout: float = 30.0) -> None:
        self._company_slugs = company_slugs
        self._timeout = timeout

    @property
    def source_name(self) -> str:
        return "lever"

    async def fetch_jobs(self) -> list[Job]:
        """Fetch jobs from all configured Lever companies."""
        all_jobs: list[Job] = []

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for slug in self._company_slugs:
                try:
                    jobs = await self._fetch_company(client, slug)
                    all_jobs.extend(jobs)
                    logger.info("Lever company '%s': fetched %d jobs", slug, len(jobs))
                except Exception:
                    logger.exception("Failed to fetch Lever company '%s'", slug)

        return all_jobs

    async def _fetch_company(
        self, client: httpx.AsyncClient, slug: str
    ) -> list[Job]:
        """Fetch postings for a single company with retry."""
        url = f"{BASE_URL}/{slug}"
        params = {"mode": "json"}

        for attempt in range(3):
            resp = await client.get(url, params=params)
            if resp.status_code == 429:
                wait = 2 ** attempt
                logger.warning("Lever rate-limited, retrying in %ds …", wait)
                import asyncio
                await asyncio.sleep(wait)
                continue
            resp.raise_for_status()
            break
        else:
            raise httpx.HTTPStatusError(
                "Rate limited after retries",
                request=resp.request,
                response=resp,
            )

        data = resp.json()
        if not isinstance(data, list):
            data = []
        return [self._normalize(item, slug) for item in data]

    @staticmethod
    def _normalize(raw: dict, company_slug: str) -> Job:
        """Transform Lever JSON into a normalized Job."""
        # Lever uses nested categories for location/team
        categories = raw.get("categories", {})
        location = categories.get("location", "") or ""

        # Lever timestamps are Unix ms
        created_ms = raw.get("createdAt", 0)
        try:
            created = datetime.fromtimestamp(created_ms / 1000, tz=timezone.utc)
        except (ValueError, OSError, TypeError):
            created = datetime.now(timezone.utc)

        # Build description from lists + description text
        desc_parts: list[str] = []
        for section in raw.get("lists", []):
            desc_parts.append(section.get("text", ""))
            desc_parts.append(section.get("content", ""))
        desc_parts.append(raw.get("descriptionPlain", "") or raw.get("description", ""))
        description = "\n".join(p for p in desc_parts if p)

        return Job(
            job_id=f"lv-{raw['id']}",
            company=company_slug,
            role=raw.get("text", ""),
            description=description,
            location=location,
            url=raw.get("hostedUrl", "") or raw.get("applyUrl", ""),
            source="lever",
            created_at=created,
        )
