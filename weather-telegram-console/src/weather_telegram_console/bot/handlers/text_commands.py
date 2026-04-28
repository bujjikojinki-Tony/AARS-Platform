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

from weather_telegram_console.bot.handlers.market import market_handler
from weather_telegram_console.bot.handlers.operations_monitor import operations_monitor_handler
from weather_telegram_console.bot.handlers.opportunities import opportunities_handler
from weather_telegram_console.bot.handlers.monitoring import monitoring_handler
from weather_telegram_console.bot.handlers.signals import signals_handler
from weather_telegram_console.bot.handlers.status import status_handler
from weather_telegram_console.bot.handlers.timeline import timeline_handler

logger = logging.getLogger(__name__)


async def text_command_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = getattr(update, "message", None)
    if not message or not getattr(message, "text", None):
        return

    command = str(message.text).strip().lower()
    logger.info("text_command_router invoked: %s", command)
    if command in {"market", "/market"}:
        await market_handler(update, context)
        return
    if command in {"opportunities", "/opportunities", "opportunity", "/opportunity"}:
        await opportunities_handler(update, context)
        return
    if command in {"monitor", "/monitor", "focus", "/focus"}:
        await operations_monitor_handler(update, context)
        return
    if command in {"signal", "signals", "/signal", "/signals"}:
        await signals_handler(update, context)
        return
    if command in {"status", "/status"}:
        await status_handler(update, context)
        return
    if command in {"monitoring", "/monitoring", "scanstatus", "/scanstatus", "alerts", "/alerts", "anomalies", "/anomalies"}:
        await monitoring_handler(update, context)
        return
    if command in {"timeline", "/timeline"}:
        await timeline_handler(update, context)
        return
