from __future__ import annotations

import logging
from typing import Any

try:
    from telegram import Update
    from telegram.ext import ContextTypes
except ModuleNotFoundError:  # pragma: no cover - local offline test fallback
    Update = Any

    class ContextTypes:
        DEFAULT_TYPE = Any

from weather_telegram_console.bot.formatters.market_card import format_market_card
from weather_telegram_console.bot.handlers.message_chunks import split_markdown_message
from weather_telegram_console.integrations.market_api import MarketAPI

logger = logging.getLogger(__name__)


async def market_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("market_handler invoked")
    market_api = MarketAPI()
    args = getattr(context, "args", None) or []
    market_id = str(args[0]).strip() if args else None

    try:
        payload = market_api.load_market_summary(market_id)
    except FileNotFoundError as exc:
        if update.message:
            await update.message.reply_text(str(exc))
        return
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.exception("market_handler failed to load summary")
        if update.message:
            await update.message.reply_text(f"Market load failed: {exc}")
        return

    if update.message:
        try:
            for chunk in split_markdown_message(format_market_card(payload)):
                await update.message.reply_text(
                    text=chunk,
                    parse_mode="Markdown",
                )
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.exception("market_handler failed to send message")
            await update.message.reply_text(f"Market render failed: {exc}")
