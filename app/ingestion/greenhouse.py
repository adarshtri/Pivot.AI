"""Greenhouse public job-board API client.

Docs: https://developers.greenhouse.io/job-board.html
Endpoint: GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from app.models.job import Job

logger = logging.getLogger(__name__)

BASE_URL = "https://boards-api.greenhouse.io/v1/boards"


class GreenhouseProvider:
    """Fetches jobs from one or more Greenhouse board tokens."""

    def __init__(self, board_tokens: list[str], timeout: float = 30.0) -> None:
        self._board_tokens = board_tokens
        self._timeout = timeout

    @property
    def source_name(self) -> str:
        return "greenhouse"

    async def fetch_jobs(self) -> list[Job]:
        """Fetch jobs from all configured Greenhouse boards."""
        all_jobs: list[Job] = []

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for token in self._board_tokens:
                try:
                    jobs = await self._fetch_board(client, token)
                    all_jobs.extend(jobs)
                    logger.info("Greenhouse board '%s': fetched %d jobs", token, len(jobs))
                except Exception:
                    logger.exception("Failed to fetch Greenhouse board '%s'", token)

        return all_jobs

    async def _fetch_board(self, client: httpx.AsyncClient, token: str) -> list[Job]:
        """Fetch a single board with retry."""
        url = f"{BASE_URL}/{token}/jobs"
        params = {"content": "true"}

        for attempt in range(3):
            resp = await client.get(url, params=params)
            if resp.status_code == 429:
                # Rate limited — back off
                wait = 2 ** attempt
                logger.warning("Greenhouse rate-limited, retrying in %ds …", wait)
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
        return [self._normalize(item, token) for item in data.get("jobs", [])]

    @staticmethod
    def _normalize(raw: dict, board_token: str) -> Job:
        """Transform Greenhouse JSON into a normalized Job."""
        location_name = ""
        if raw.get("location"):
            location_name = raw["location"].get("name", "")

        updated = raw.get("updated_at") or raw.get("created_at", "")
        try:
            created = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            created = datetime.now(timezone.utc)

        return Job(
            job_id=f"gh-{raw['id']}",
            company=board_token,
            role=raw.get("title", ""),
            description=raw.get("content", ""),
            location=location_name,
            url=raw.get("absolute_url", ""),
            source="greenhouse",
            created_at=created,
        )
