import logging
from typing import Any

try:
    from telegram import Update
    from telegram.ext import ContextTypes
except ModuleNotFoundError:  # pragma: no cover - local offline test fallback
    Update = Any

    class ContextTypes:
        DEFAULT_TYPE = Any

from weather_telegram_console.bot.formatters.status_card import format_status_card
from weather_telegram_console.bot.handlers.message_chunks import split_markdown_message
from weather_telegram_console.integrations.status_api import StatusAPI

logger = logging.getLogger(__name__)


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("status_handler invoked")
    try:
        report = StatusAPI().load_latest_status()
    except FileNotFoundError as exc:
        if update.message:
            await update.message.reply_text(str(exc))
        return
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.exception("status_handler failed to load status")
        if update.message:
            await update.message.reply_text(f"Status load failed: {exc}")
        return

    if update.message:
        try:
            for chunk in split_markdown_message(format_status_card(report)):
                await update.message.reply_text(
                    text=chunk,
                    parse_mode="Markdown",
                )
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.exception("status_handler failed to send message")
            await update.message.reply_text(f"Status render failed: {exc}")
