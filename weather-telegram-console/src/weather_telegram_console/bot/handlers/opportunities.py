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

from weather_telegram_console.bot.formatters.opportunity_board_card import format_opportunity_board_card
from weather_telegram_console.bot.handlers.message_chunks import split_markdown_message
from weather_telegram_console.integrations.opportunity_api import OpportunityAPI

logger = logging.getLogger(__name__)


async def opportunities_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("opportunities_handler invoked")
    args = getattr(context, "args", None) or []
    city = " ".join(str(arg).strip() for arg in args if str(arg).strip()) or None
    try:
        payload = OpportunityAPI().load_opportunity_board(city)
    except FileNotFoundError as exc:
        if update.message:
            await update.message.reply_text(str(exc))
        return
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.exception("opportunities_handler failed to load opportunity board")
        if update.message:
            await update.message.reply_text(f"Opportunity load failed: {exc}")
        return

    if update.message:
        try:
            for chunk in split_markdown_message(format_opportunity_board_card(payload)):
                await update.message.reply_text(
                    text=chunk,
                    parse_mode="Markdown",
                )
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.exception("opportunities_handler failed to send message")
            await update.message.reply_text(f"Opportunity render failed: {exc}")
