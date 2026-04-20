from __future__ import annotations

from typing import Any

try:
    from telegram import Update
    from telegram.ext import ContextTypes
except ModuleNotFoundError:  # pragma: no cover - local offline test fallback
    Update = Any

    class ContextTypes:
        DEFAULT_TYPE = Any

from weather_telegram_console.bot.formatters.timeline_card import format_timeline_card
from weather_telegram_console.integrations.market_api import MarketAPI


async def timeline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    market_api = MarketAPI()
    args = getattr(context, "args", None) or []
    market_id = str(args[0]).strip() if args else None

    try:
        entries = market_api.load_market_timeline(market_id)
    except FileNotFoundError as exc:
        if update.message:
            await update.message.reply_text(str(exc))
        return

    resolved_market_id = str((entries[0] or {}).get("market_id") or market_id or "-")
    if update.message:
        await update.message.reply_text(
            text=format_timeline_card(resolved_market_id, entries),
            parse_mode="Markdown",
        )
