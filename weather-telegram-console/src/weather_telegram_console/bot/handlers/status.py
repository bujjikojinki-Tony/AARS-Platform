from typing import Any

try:
    from telegram import Update
    from telegram.ext import ContextTypes
except ModuleNotFoundError:  # pragma: no cover - local offline test fallback
    Update = Any

    class ContextTypes:
        DEFAULT_TYPE = Any

from weather_telegram_console.bot.formatters.status_card import format_status_card
from weather_telegram_console.integrations.status_api import StatusAPI


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        report = StatusAPI().load_latest_status()
    except FileNotFoundError as exc:
        if update.message:
            await update.message.reply_text(str(exc))
        return

    if update.message:
        await update.message.reply_text(
            text=format_status_card(report),
            parse_mode="Markdown",
        )
