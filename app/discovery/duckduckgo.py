"""DuckDuckGo Search client for discovering ATS boards (Fallback)."""

import asyncio
from ddgs import DDGS
from urllib.parse import urlparse

class DuckDuckGoClient:
    """Client for performing web searches using DuckDuckGo (via ddgs package)."""

    async def search(self, query: str, count: int = 10) -> list[dict]:
        """
        Execute a DuckDuckGo search and return matching results.
        Runs synchronously under the hood, so we wrap it in asyncio.to_thread.
        """
        def _do_search():
            urls = []
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=count))
                    for r in results:
                        if "href" in r:
                            # Basic validation to ensure it's a URL
                            parsed = urlparse(r["href"])
                            if parsed.scheme in ("http", "https"):
                                urls.append({"url": r["href"]})
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"DuckDuckGo search failed: {e}")
            return urls

        return await asyncio.to_thread(_do_search)
