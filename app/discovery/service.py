"""Company discovery service.

Discovers companies from user goals via Brave Search, extracts ATS board
tokens from result URLs, validates them, and stores in MongoDB.
"""

from __future__ import annotations
from typing import Any, Protocol, runtime_checkable
import logging
import re
from datetime import datetime, timezone

import httpx
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.discovery.search import BraveSearchClient
from app.scoring.llm import LLMProvider, OllamaClient, GroqClient

logger = logging.getLogger(__name__)

# ── Regex patterns to extract board tokens from URLs ─────────────────────────

GREENHOUSE_PATTERN = re.compile(
    r"boards\.greenhouse\.io/([a-zA-Z0-9_-]+)"
)
LEVER_PATTERN = re.compile(
    r"(?:jobs\.)?lever\.co/([a-zA-Z0-9_-]+)"
)
ASHBY_PATTERN = re.compile(
    r"jobs\.ashbyhq\.com/([a-zA-Z0-9_-]+)"
)


def _build_search_queries(keywords: list[str]) -> list[str]:
    """Generate search queries from a list of user goal keywords.

    Builds queries scoped to Greenhouse, Lever, and Ashby job boards.
    """
    queries: list[str] = []

    if not keywords:
        return []

    # Create queries scoped to ATS sites
    site_filter = "site:lever.co OR site:boards.greenhouse.io OR site:jobs.ashbyhq.com"

    # Batch keywords into groups to avoid overly long queries
    for kw in keywords:
        queries.append(f'"{kw}" ({site_filter})')

    return queries


def _extract_tokens(results: list[dict]) -> dict[str, set[str]]:
    """Extract Greenhouse board tokens, Lever company slugs, and Ashby slugs from URLs."""
    tokens: dict[str, set[str]] = {"greenhouse": set(), "lever": set(), "ashby": set()}

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

        as_match = ASHBY_PATTERN.search(url)
        if as_match:
            slug = as_match.group(1).lower()
            if slug not in ("jobs", "postings", "api"):
                tokens["ashby"].add(slug)

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


async def _probe_ashby(slug: str) -> bool:
    """Check if an Ashby company slug returns valid postings."""
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                # Ashby returns metadata and jobs list
                return len(data.get("jobs", [])) > 0
    except Exception:
        pass
    return False


class DiscoveryService:
    """Discovers companies from user goals and stores them in MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase, search_client: Any) -> None:
        self._db = db
        self._search = search_client
        self._llm_client: LLMProvider | None = None

    async def _get_llm_client(self) -> LLMProvider:
        from app.scoring.llm_factory import LLMFactory
        return await LLMFactory.get_provider(self._db)

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
        provider_name = self._search.__class__.__name__
        logger.info("Discovery: %d queries from user goals using %s", len(queries), provider_name)

        # 3. Search and extract tokens
        all_results: list[dict] = []
        for query in queries:
            try:
                results = await self._search.search(query)
                all_results.extend(results)
            except Exception:
                logger.exception("Search failed for query: %s", query)

        tokens = _extract_tokens(all_results)
        total_found = len(tokens["greenhouse"]) + len(tokens["lever"]) + len(tokens["ashby"])
        logger.info(
            "Extracted tokens — Greenhouse: %d, Lever: %d, Ashby: %d",
            len(tokens["greenhouse"]),
            len(tokens["lever"]),
            len(tokens["ashby"]),
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

        for slug in tokens["ashby"]:
            if await _probe_ashby(slug):
                await self._store_company(slug, "ashby")
                added += 1
                logger.info("✅ Discovered Ashby company: %s", slug)
            else:
                logger.debug("❌ Invalid Ashby slug: %s", slug)

        summary = {
            "queries_run": len(queries),
            "tokens_found": total_found,
            "companies_added": added,
        }
        logger.info("Discovery complete: %s", summary)
        return summary

    async def run_enrichment(self, force: bool = False) -> dict:
        """Retroactively enrich existing companies with metadata using batching."""
        logger.info("Starting retroactive company enrichment (force=%s)", force)
        
        # 1. Find companies in JOBS that are missing from COMPANIES entirely
        all_job_companies = await self._db.jobs.distinct("company")
        existing_names = await self._db.companies.distinct("name")
        missing_names = [c for c in all_job_companies if c and c not in existing_names]
        
        # 2. Find existing companies that need metadata (description + domain) unless forced
        if force:
            query = {}
        else:
            query = {
                "$or": [
                    {"description": {"$in": ["", None]}},
                    {"domain": {"$in": ["", None]}}
                ]
            }
        
        companies_to_enrich = await self._db.companies.find(query).to_list(length=1000)
        
        # 3. Add placeholders for missing companies (so they get enriched too)
        for name in missing_names:
            companies_to_enrich.append({"name": name, "is_new_placeholder": True})
            
        total_to_enrich = len(companies_to_enrich)
        logger.info("Found %d companies to research/enrich (%d from ingestion)", total_to_enrich, len(missing_names))
        
        enriched_count = 0
        batch_size = 5
        
        for i in range(0, total_to_enrich, batch_size):
            batch = companies_to_enrich[i : i + batch_size]
            names = [doc["name"] for doc in batch if doc.get("name")]
            if not names: continue
            
            logger.info("Enriching batch [%d/%d]: %s", i + len(names), total_to_enrich, names)
            results = await self._enrich_companies_batch(names)
            
            # Map results by name for easy lookup
            results_map = {r.get("name"): r for r in results if r.get("name")}
            
            for doc in batch:
                name = doc["name"]
                enrichment = results_map.get(name)
                if not enrichment:
                    # Fallback to individual if batch missed it or failed
                    logger.warning("Batch missed %s, falling back to individual", name)
                    enrichment = await self._enrich_company(name)
                
                if enrichment:
                    update_fields = {
                        "name": name,
                        "domain": enrichment.get("domain") or "",
                        "size": enrichment.get("size") or "",
                        "stage": enrichment.get("stage") or "",
                        "description": enrichment.get("description") or "",
                        "updated_at": datetime.now(timezone.utc)
                    }
                    
                    if doc.get("is_new_placeholder") or doc.get("source") == "ingested":
                        # Try to identify real source from job URLs
                        source = doc.get("source", "ingested")
                        job_sample = await self._db.jobs.find_one({"company": name})
                        if job_sample:
                            u = job_sample.get("url", "")
                            if GREENHOUSE_PATTERN.search(u):
                                source = "greenhouse"
                            elif LEVER_PATTERN.search(u):
                                source = "lever"
                            elif ASHBY_PATTERN.search(u):
                                source = "ashby"

                        # Insert/Update discovered company info
                        await self._db.companies.update_one(
                            {"name": name},
                            {
                                "$set": {
                                    **update_fields,
                                    "slug": name.lower().replace(" ", "-"),
                                    "source": source,
                                    "discovered_via": "ingestion",
                                },
                                "$setOnInsert": {"created_at": datetime.now(timezone.utc)}
                            },
                            upsert=True
                        )
                    else:
                        # Update existing
                        await self._db.companies.update_one({"_id": doc["_id"]}, {"$set": update_fields})
                    
                    enriched_count += 1
                    
        return {"status": "completed", "enriched_count": enriched_count}

    async def _enrich_companies_batch(self, names: list[str]) -> list[dict]:
        """Use LLM to generate metadata for multiple companies in one call."""
        if not names: return []
        llm = await self._get_llm_client()
        names_str = ", ".join(names)
        
        prompt = f"""You are a company research assistant. Provide metadata for these companies: {names_str}.
        
        For each company, provide:
        - name: The company name (EXACTLY as provided in the list)
        - domain: Potential web domain (e.g. openai.com)
        - size: Number of employees (e.g. 100-500, 10,000+)
        - stage: Type (e.g. Series A, Public, Startup, Private)
        - description: Concise 1-2 sentence description.
        
        Return a JSON object with a key "companies" containing a list of these objects.
        Return ONLY the JSON object."""
        
        try:
            res_text = await llm.generate_text(prompt, temperature=0.0)
            import json, re
            match = re.search(r"\{.*\}", res_text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return data.get("companies", [])
        except Exception:
            logger.exception("Batch enrichment failed")
        return []

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
            "ashby": {t for t in tokens["ashby"] if (t, "ashby") not in existing},
        }
        skipped = (len(tokens["greenhouse"]) + len(tokens["lever"]) + len(tokens["ashby"])) - (
            len(filtered["greenhouse"]) + len(filtered["lever"]) + len(filtered["ashby"])
        )

        if skipped:
            logger.info("Skipped %d already-known companies", skipped)
        return filtered

    async def _enrich_company(self, name: str) -> dict:
        """Use LLM to generate description, domain, size, and type for a company."""
        llm = await self._get_llm_client()
        prompt = f"""You are a company research assistant. Provide metadata for the company: {name}.
        
        Capture the following in JSON format:
        - domain: Potential web domain (e.g. openai.com)
        - size: Number of employees (e.g. 100-500, 10,000+)
        - stage: Type (e.g. Series A, Public, Startup, Private)
        - description: Concise 1-2 sentence description including their main industry and focus.
        
        Return ONLY the JSON object."""
        
        try:
            res_text = await llm.generate_text(prompt, temperature=0.0)
            # Simple extractor for json
            import json
            import re
            match = re.search(r"\{.*\}", res_text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception:
            logger.exception("Failed to enrich company %s", name)
        
        return {}

    async def _store_company(self, name: str, source: str) -> None:
        """Upsert a discovered company into MongoDB with enrichment."""
        now = datetime.now(timezone.utc)
        
        # Check if we already have this company name enriched elsewhere
        # This prevents re-enriching if discovered from a different ATS source
        existing = await self._db.companies.find_one({
            "name": name, 
            "description": {"$ne": ""}
        })
        
        if existing:
            logger.info("Company %s already enriched, reusing metadata.", name)
            enrichment = {
                "domain": existing.get("domain") or "",
                "stage": existing.get("stage") or "",
                "size": existing.get("size") or "",
                "description": existing.get("description") or ""
            }
        else:
            # Enrich before storing
            enrichment = await self._enrich_company(name)
        
        await self._db.companies.update_one(
            {"name": name, "source": source},
            {
                "$set": {
                    "name": name,
                    "slug": name,
                    "source": source,
                    "domain": enrichment.get("domain") or "",
                    "stage": enrichment.get("stage") or "",
                    "size": enrichment.get("size") or "",
                    "description": enrichment.get("description") or "",
                    "discovered_via": "brave_search",
                    "updated_at": now,
                },
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )
