"""Telegram utility functions for sending messages."""

import logging
import httpx

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org/bot"

async def send_telegram_message(token: str, chat_id: int, text: str):
    """Send a message to a specific Telegram chat using the provided bot token."""
    url = f"{TELEGRAM_API_BASE}{token}/sendMessage"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
