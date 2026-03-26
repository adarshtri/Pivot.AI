"""Company discovery service.

Discovers companies from user goals via Brave Search, extracts ATS board
tokens from result URLs, validates them, and stores in MongoDB.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

import httpx
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.discovery.search import BraveSearchClient

logger = logging.getLogger(__name__)

# ── Regex patterns to extract board tokens from URLs ─────────────────────────

GREENHOUSE_PATTERN = re.compile(
    r"boards\.greenhouse\.io/([a-zA-Z0-9_-]+)"
)
LEVER_PATTERN = re.compile(
    r"(?:jobs\.)?lever\.co/([a-zA-Z0-9_-]+)"
)


def _build_search_queries(keywords: list[str]) -> list[str]:
    """Generate search queries from a list of user goal keywords.

    Builds queries scoped to Greenhouse and Lever job boards.
    """
    queries: list[str] = []

    if not keywords:
        return []

    # Create queries scoped to ATS sites
    site_filter = "site:lever.co OR site:boards.greenhouse.io"

    # Batch keywords into groups to avoid overly long queries
    for kw in keywords:
        queries.append(f'"{kw}" ({site_filter})')

    return queries


def _extract_tokens(results: list[dict]) -> dict[str, set[str]]:
    """Extract Greenhouse board tokens and Lever company slugs from URLs."""
    tokens: dict[str, set[str]] = {"greenhouse": set(), "lever": set()}

    for r in results:
        url = r.get("url", "")

        gh_match = GREENHOUSE_PATTERN.search(url)
        if gh_match:
            token = gh_match.group(1).lower()
            # Filter out generic/non-company paths
            if token not in ("embed", "job_app", "jobs", "include"):
                tokens["greenhouse"].add(token)

        lv_match = LEVER_PATTERN.search(url)
        if lv_match:
            slug = lv_match.group(1).lower()
            if slug not in ("jobs", "postings", "api"):
                tokens["lever"].add(slug)

    return tokens


async def _probe_greenhouse(token: str) -> bool:
    """Check if a Greenhouse board token returns valid jobs."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return len(data.get("jobs", [])) > 0
    except Exception:
        pass
    return False


async def _probe_lever(slug: str) -> bool:
    """Check if a Lever company slug returns valid postings."""
    url = f"https://api.lever.co/v0/postings/{slug}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params={"mode": "json", "limit": 1})
            if resp.status_code == 200:
                data = resp.json()
                return isinstance(data, list) and len(data) > 0
    except Exception:
        pass
    return False


class DiscoveryService:
    """Discovers companies from user goals and stores them in MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase, search_client: BraveSearchClient) -> None:
        self._db = db
        self._search = search_client

    async def run(self) -> dict:
        """Execute a full discovery cycle across all users' goals.

        Returns summary: {"queries_run": N, "tokens_found": M, "companies_added": K}
        """
        # 1. Gather all unique goal texts from users
        keywords = await self._collect_goals()
        if not keywords:
            logger.warning("No user goals found — skipping discovery.")
            return {"queries_run": 0, "tokens_found": 0, "companies_added": 0}

        # 2. Build search queries
        queries = _build_search_queries(keywords)
        logger.info("Discovery: %d queries from user goals", len(queries))

        # 3. Search and extract tokens
        all_results: list[dict] = []
        for query in queries:
            try:
                results = await self._search.search(query)
                all_results.extend(results)
            except Exception:
                logger.exception("Search failed for query: %s", query)

        tokens = _extract_tokens(all_results)
        total_found = len(tokens["greenhouse"]) + len(tokens["lever"])
        logger.info(
            "Extracted tokens — Greenhouse: %d, Lever: %d",
            len(tokens["greenhouse"]),
            len(tokens["lever"]),
        )

        # 4. Filter out already-known companies
        tokens = await self._filter_known(tokens)

        # 5. Probe and store valid companies
        added = 0
        for token in tokens["greenhouse"]:
            if await _probe_greenhouse(token):
                await self._store_company(token, "greenhouse")
                added += 1
                logger.info("✅ Discovered Greenhouse company: %s", token)
            else:
                logger.debug("❌ Invalid Greenhouse token: %s", token)

        for slug in tokens["lever"]:
            if await _probe_lever(slug):
                await self._store_company(slug, "lever")
                added += 1
                logger.info("✅ Discovered Lever company: %s", slug)
            else:
                logger.debug("❌ Invalid Lever slug: %s", slug)

        summary = {
            "queries_run": len(queries),
            "tokens_found": total_found,
            "companies_added": added,
        }
        logger.info("Discovery complete: %s", summary)
        return summary

    async def _collect_goals(self) -> list[str]:
        """Merge goal texts from all users into a combined set of keywords."""
        keywords: set[str] = set()
        async for user in self._db.users.find({"goals": {"$exists": True}}, {"goals": 1}):
            goals = user.get("goals", [])
            for g in goals:
                if isinstance(g, dict) and "text" in g:
                    g_type = g.get("type", "Target Role")
                    if g_type in ("Domain", "Target Role"):
                        keywords.add(g["text"])

        return list(keywords)

    async def _filter_known(self, tokens: dict[str, set[str]]) -> dict[str, set[str]]:
        """Remove tokens that are already in the companies collection."""
        existing = set()
        async for doc in self._db.companies.find({}, {"name": 1, "source": 1}):
            existing.add((doc["name"], doc.get("source", "")))

        filtered = {
            "greenhouse": {t for t in tokens["greenhouse"] if (t, "greenhouse") not in existing},
            "lever": {t for t in tokens["lever"] if (t, "lever") not in existing},
        }
        skipped = (len(tokens["greenhouse"]) + len(tokens["lever"])) - (
            len(filtered["greenhouse"]) + len(filtered["lever"])
        )
        if skipped:
            logger.info("Skipped %d already-known companies", skipped)
        return filtered

    async def _store_company(self, name: str, source: str) -> None:
        """Upsert a discovered company into MongoDB."""
        now = datetime.now(timezone.utc)
        await self._db.companies.update_one(
            {"name": name, "source": source},
            {
                "$set": {
                    "name": name,
                    "source": source,
                    "discovered_via": "brave_search",
                    "updated_at": now,
                },
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )
