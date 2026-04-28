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

from weather_telegram_console.bot.formatters.monitoring_card import format_monitoring_card
from weather_telegram_console.bot.handlers.message_chunks import split_markdown_message
from weather_telegram_console.integrations.monitoring_api import MonitoringAPI

logger = logging.getLogger(__name__)


async def monitoring_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("monitoring_handler invoked")
    try:
        payload = MonitoringAPI().load_latest_monitoring_signals()
    except FileNotFoundError as exc:
        if update.message:
            await update.message.reply_text(str(exc))
        return
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.exception("monitoring_handler failed to load monitoring signals")
        if update.message:
            await update.message.reply_text(f"Monitoring load failed: {exc}")
        return

    if update.message:
        try:
            for chunk in split_markdown_message(format_monitoring_card(payload)):
                await update.message.reply_text(
                    text=chunk,
                    parse_mode="Markdown",
                )
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.exception("monitoring_handler failed to send message")
            await update.message.reply_text(f"Monitoring render failed: {exc}")
