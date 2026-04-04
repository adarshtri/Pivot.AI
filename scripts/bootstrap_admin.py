"""Bootstrap script -- Creates the default local developer user with admin privileges."""

import asyncio
import os
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient


async def main() -> None:
    user_id = "dev_user"
    print(f"🌱 Bootstrapping Pivot.AI Local Developer: {user_id}...")
    
    # 1. Connect to MongoDB
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongodb_url)
    db = client.pivot_ai
    
    now = datetime.now(timezone.utc)
    
    # 2. Upsert user_id with admin access
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {
            "is_admin": True,
            "updated_at": now
        }},
        upsert=True
    )
    
    # 3. Verify
    user = await db.users.find_one({"user_id": user_id})
    print(f"✅ Created local developer profile:")
    print(f"   • User ID: {user['user_id']}")
    print(f"   • Admin Status: {user['is_admin']}")
    print(f"\n✨ Bootstrap complete! You may now open http://localhost:3000 and access the Admin panel.")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
