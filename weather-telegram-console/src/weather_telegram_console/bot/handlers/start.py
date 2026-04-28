from typing import Any

try:
    from telegram import Update
    from telegram.ext import ContextTypes
except ModuleNotFoundError:  # pragma: no cover - local offline test fallback
    Update = Any

    class ContextTypes:
        DEFAULT_TYPE = Any


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(
            "Weather Telegram Console is running.\n"
            "Use /status, /market, /opportunities, /timeline, or /signals."
        )
