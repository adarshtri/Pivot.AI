"""Brave Search API client for company discovery."""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


class BraveSearchClient:
    """Thin wrapper around the Brave Web Search API."""

    def __init__(self, api_key: str, timeout: float = 15.0) -> None:
        self._api_key = api_key
        self._timeout = timeout

    async def search(self, query: str, count: int = 50) -> list[dict]:
        """Run a web search and return result items.

        Each result dict has keys: 'title', 'url', 'description'.
        """
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self._api_key,
        }
        params = {"q": query, "count": min(count, 50)}

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(BRAVE_SEARCH_URL, headers=headers, params=params)
            resp.raise_for_status()

        data = resp.json()
        results = data.get("web", {}).get("results", [])
        logger.info("Brave search for '%s': %d results", query, len(results))

        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "description": r.get("description", ""),
            }
            for r in results
        ]
