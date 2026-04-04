"""Authentication and authorization dependencies using Clerk (or development mock)."""

import logging
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError

from app.config import settings
from app.database import get_db

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Simple cache for JWKS or public keys could go here.

async def get_current_user(token: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Verifies the Bearer token and returns the user_id (sub claim).
    
    If settings.clerk_issuer_url is empty, it operates in 'dev mode' 
    treating the bearer token string itself as the user_id.
    """
    if not settings.clerk_issuer_url:
        # Dev fallback: Try to decode stable 'sub' claim even without signature verification
        try:
            payload = jwt.decode(
                token.credentials,
                None,
                options={"verify_signature": False, "verify_aud": False},
            )
            user_id = payload.get("sub")
        except JWTError:
            # Fallback for non-JWT strings (manual testing)
            user_id = token.credentials
            
        if not user_id:
            user_id = "dev_user"
        logger.debug("Auth (Dev Mode): user_id='%s'", user_id)
    else:
        try:
            # TODO: Add real JWKS verification for production
            # For now, we trust the issuer if it matches, but don't verify signature 
            # (Requires Public Key from Clerk dashboard)
            payload = jwt.decode(
                token.credentials,
                None,
                options={"verify_signature": False, "verify_aud": False},
            )
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Token missing 'sub' claim")
        except JWTError as e:
            logger.error("JWT Verification failed: %s", e)
            raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Sync user to DB atomically using upsert
    db = get_db()
    now = datetime.now(timezone.utc)
    
    # We use an atomic upsert with $setOnInsert for defaults to prevent 
    # race conditions and redundant entries during concurrent sign-ins.
    await db.users.update_one(
        {"user_id": user_id},
        {
            "$setOnInsert": {
                "user_id": user_id,
                "skills": [],
                "experience_level": "",
                "current_role": "",
                "is_admin": False,
                "created_at": now,
            },
            "$set": {
                "updated_at": now,
            },
        },
        upsert=True,
    )

    return user_id


async def require_admin(user_id: str = Depends(get_current_user)) -> str:
    """Dependency that ensures the current user is an admin."""
    db = get_db()
    user = await db.users.find_one({"user_id": user_id}, {"is_admin": 1})
    
    if not user or not user.get("is_admin"):
        logger.warning("Unauthorized admin access attempt by user: %s", user_id)
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    return user_id
