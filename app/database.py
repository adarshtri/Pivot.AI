"""Async MongoDB connection and index management via Motor."""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_db() -> None:
    """Create the Motor client and ensure indexes exist."""
    global _client, _db
    _client = AsyncIOMotorClient(settings.mongodb_url)
    _db = _client[settings.database_name]

    # --- indexes ---
    await _db.jobs.create_index("job_id", unique=True)
    await _db.jobs.create_index("company")
    await _db.jobs.create_index("source")
    await _db.users.create_index("user_id", unique=True)
    await _db.companies.create_index("name", unique=True)


async def close_db() -> None:
    """Gracefully close the Motor client."""
    global _client, _db
    if _client:
        _client.close()
    _client = None
    _db = None


def get_db() -> AsyncIOMotorDatabase:
    """Return the database instance. Raises if not connected."""
    if _db is None:
        raise RuntimeError("Database not connected. Call connect_db() first.")
    return _db
