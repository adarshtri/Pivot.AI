"""Job Ingestion Tool for Pivot.AI (Playbook-Compatible)."""

import logging
from app.ingestion.service import IngestionService
from app.ingestion.ashby import AshbyProvider
from app.repository import FileRepository

logger = logging.getLogger("mcp.tools.ingestion")

async def ingest_jobs(source: str = "all") -> str:
    """
    Trigger the job ingestion pipeline from different sources.
    :param source: The source to ingest from (e.g., 'ashby', 'all').
    """
    logger.info(f"Starting file-based ingestion for source: {source}")
    repo = FileRepository()
    providers = [AshbyProvider(slugs=["egen"])] if source in ["ashby", "all"] else []
    service = IngestionService(repo, providers)
    summary = await service.run()
    return f"✅ Ingestion complete (File-Based): {summary}"
