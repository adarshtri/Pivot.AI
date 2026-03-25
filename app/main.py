"""Pivot.AI — FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import close_db, connect_db
from app.ingestion.scheduler import start_scheduler, stop_scheduler
from app.routers import admin, discovery, goals, jobs, pipeline, profile

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup/shutdown: DB connection and ingestion scheduler."""
    logger.info("Starting Pivot.AI …")
    await connect_db()
    start_scheduler()
    yield
    stop_scheduler()
    await close_db()
    logger.info("Pivot.AI shut down.")


app = FastAPI(
    title="Pivot.AI",
    description="AI-native career intelligence platform",
    version="0.1.0",
    lifespan=lifespan,
)

# ── Mount routers ────────────────────────────────────────────────────────────
app.include_router(profile.router)
app.include_router(goals.router)
app.include_router(jobs.router)
app.include_router(discovery.router)
app.include_router(pipeline.router)
app.include_router(admin.router)


@app.get("/health", tags=["System"])
async def health_check():
    """Simple liveness probe."""
    return {"status": "ok"}
