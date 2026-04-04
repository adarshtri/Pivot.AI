"""Seed script — creates a sample user profile + goals via the API.

Usage:
    python -m scripts.seed
"""

import httpx
import sys


BASE_URL = "http://localhost:8000/api/v1"


def main() -> None:
    user_id = "dev_user"
    print(f"🌱 Seeding Pivot.AI for {user_id} …\n")

    with httpx.Client(base_url=BASE_URL, timeout=10) as client:
        # 1. Health check
        resp = client.get("/health")
        if resp.status_code != 200:
            print("❌ Server not reachable. Is it running on port 8000?")
            sys.exit(1)
        print("✅ Server healthy\n")

        # 2. Create profile
        profile = {
            "user_id": user_id,
            "skills": ["backend", "distributed systems", "AI", "LLM"],
            "experience_level": "L5",
            "current_role": "Senior Software Engineer",
        }
        resp = client.post("/profile/", json=profile)
        resp.raise_for_status()
        print(f"✅ Profile created: {resp.json()}\n")

        # 3. Create goals
        goals = {
            "user_id": user_id,
            "target_roles": ["AI Engineer", "ML Infrastructure Engineer", "Backend Tech Lead"],
            "domains": ["AI", "systems", "infrastructure"],
            "career_direction": "ownership and technical leadership in AI systems",
        }
        resp = client.post("/goals/", json=goals)
        resp.raise_for_status()
        print(f"✅ Goals created: {resp.json()}\n")

        # 4. Read back
        resp = client.get(f"/profile/{user_id}")
        print(f"📋 Profile: {resp.json()}\n")

        resp = client.get(f"/goals/{user_id}")
        print(f"🎯 Goals: {resp.json()}\n")

        # 5. Trigger ingestion
        print("🔄 Triggering ingestion …")
        resp = client.post("/jobs/ingest")
        print(f"📊 Ingestion result: {resp.json()}\n")

        # 6. List jobs
        resp = client.get("/jobs/", params={"limit": 5})
        jobs = resp.json()
        print(f"📦 Jobs in DB: {len(jobs)}")
        for j in jobs[:5]:
            print(f"   • {j['role']} @ {j['company']} ({j['source']})")

    print("\n✨ Seed complete!")


if __name__ == "__main__":
    main()
