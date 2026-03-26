"""Telegram multi-bot webhook router."""

import logging
import httpx
from fastapi import APIRouter, Request, HTTPException
from app.database import get_db
from app.telegram_utils import send_telegram_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/telegram", tags=["Telegram"])


@router.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    """
    Dynamic webhook endpoint for multiple Telegram bots.
    Each user has their own bot token, which acts as the unique path identifier.
    """
    db = get_db()
    
    # 1. Find the user associated with this bot token
    user = await db.users.find_one({"telegram_token": token})
    if not user:
        logger.warning(f"Received webhook for unknown token: {token[:10]}...")
        # We return 200 to Telegram to stop retries, even if token is unknown
        return {"status": "ignored", "reason": "unknown_token"}

    user_id = user["user_id"]
    
    # 2. Parse the update from Telegram
    try:
        data = await request.json()
    except Exception:
        return {"status": "error", "message": "invalid_json"}

    # Handle messages
    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        # A. Handle /start - Link Chat ID
        if text.startswith("/start"):
            await db.users.update_one(
                {"user_id": user_id},
                {"$set": {"telegram_chat_id": str(chat_id)}}
            )

            welcome_text = (
                "<b>🚀 Pivot.AI Bot Activated!</b>\n\n"
                "I am now linked to your profile. I'll notify you whenever I find "
                "high-quality job matches for your goals.\n\n"
                "Try /status to see your current pipeline."
            )
            await send_telegram_message(token, chat_id, welcome_text)

        # B. Handle /status - Quick Stats
        elif text.startswith("/status"):
            # Aggregate pipeline counts
            counts_cursor = db.pipeline.aggregate([
                {"$match": {"user_id": user_id}},
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ])
            counts_dict = {
                "recommended": 0,
                "saved": 0,
                "applied": 0,
                "ignored": 0
            }
            async for item in counts_cursor:
                if item["_id"] in counts_dict:
                    counts_dict[item["_id"]] = item["count"]

            status_text = (
                "<b>📊 Your Job Pipeline</b>\n\n"
                f"✨ <b>Recommended:</b> {counts_dict['recommended']}\n"
                f"📂 <b>Saved:</b> {counts_dict['saved']}\n"
                f"📝 <b>Applied:</b> {counts_dict['applied']}\n"
                f"🚫 <b>Ignored:</b> {counts_dict['ignored']}\n\n"
                "Check the dashboard for details: http://localhost:3000/jobs"
            )
            await send_telegram_message(token, chat_id, status_text)

    return {"status": "ok"}
