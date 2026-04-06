import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

class FileRepository:
    """Manages data persistence using plain JSON and Markdown files.
    
    Default location: ~/.pivot-ai/data/
    """

    def __init__(self, base_path: Optional[str] = None):
        if base_path:
            self.base_path = Path(base_path)
        else:
            self.base_path = Path.home() / ".pivot-ai" / "data"
        
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.jobs_file = self.base_path / "jobs.json"
        
        # Initialize jobs file if it doesn't exist
        if not self.jobs_file.exists():
            self._save_jobs([])

    def _load_jobs(self) -> list[dict[str, Any]]:
        """Load all jobs from the JSON file."""
        try:
            with open(self.jobs_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load jobs: {e}")
            return []

    def _save_jobs(self, jobs: list[dict[str, Any]]):
        """Save all jobs to the JSON file atomically."""
        temp_file = self.jobs_file.with_suffix(".tmp")
        try:
            with open(temp_file, "w") as f:
                json.dump(jobs, f, indent=2, default=str)
            os.replace(temp_file, self.jobs_file)
        except Exception as e:
            logger.error(f"Failed to save jobs: {e}")
            if temp_file.exists():
                os.remove(temp_file)

    async def list_jobs(self) -> list[dict[str, Any]]:
        """Return all jobs."""
        return self._load_jobs()

    async def get_job(self, job_id: str) -> Optional[dict[str, Any]]:
        """Find a job by ID."""
        jobs = self._load_jobs()
        return next((j for j in jobs if j.get("job_id") == job_id), None)

    async def upsert_job(self, job_data: dict[str, Any], sync_session_id: Optional[str] = None) -> str:
        """Insert or update a job. Returns 'inserted' or 'updated'."""
        jobs = self._load_jobs()
        job_id = job_data.get("job_id")
        
        existing_idx = next((i for i, j in enumerate(jobs) if j.get("job_id") == job_id), None)
        
        job_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        if sync_session_id:
            job_data["last_sync_id"] = sync_session_id

        if existing_idx is not None:
            # Merge existing and new data
            jobs[existing_idx].update(job_data)
            self._save_jobs(jobs)
            return "updated"
        else:
            job_data["ingested_at"] = datetime.now(timezone.utc).isoformat()
            jobs.append(job_data)
            self._save_jobs(jobs)
            return "inserted"

    async def sweep_closed_jobs(self, sync_session_id: str) -> int:
        """Mark jobs not seen in the current sync session as CLOSED."""
        jobs = self._load_jobs()
        closed_count = 0
        
        for job in jobs:
            if job.get("status") == "OPEN" and job.get("last_sync_id") != sync_session_id:
                job["status"] = "CLOSED"
                job["closed_at"] = datetime.now(timezone.utc).isoformat()
                closed_count += 1
        
        if closed_count > 0:
            self._save_jobs(jobs)
        
        return closed_count
