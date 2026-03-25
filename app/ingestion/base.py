"""Abstract interface for job data providers.

All ingestion sources (Greenhouse, Lever, etc.) implement this protocol
so they can be swapped, composed, or mocked without touching the orchestrator.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.models.job import Job


@runtime_checkable
class JobProvider(Protocol):
    """Contract every job-data source must satisfy."""

    @property
    def source_name(self) -> str:
        """Human-readable source identifier (e.g. 'greenhouse')."""
        ...

    async def fetch_jobs(self) -> list[Job]:
        """Fetch and return normalized Job objects from the external source."""
        ...
