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

from weather_telegram_console.bot.formatters.signal_card import format_signal_card
from weather_telegram_console.bot.keyboards.signal_actions import build_signal_actions_keyboard
from weather_telegram_console.bot.handlers.message_chunks import split_markdown_message
from weather_telegram_console.integrations.signal_api import SignalAPI
from weather_telegram_console.integrations.status_api import StatusAPI
from weather_telegram_console.storage.session_repo import ApprovalRepository
from weather_telegram_console.storage.sqlite import SQLiteStore

logger = logging.getLogger(__name__)


async def signals_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("signals_handler invoked")
    signal_api = SignalAPI()

    try:
        payload = signal_api.load_latest_signal()
    except FileNotFoundError as exc:
        if update.message:
            await update.message.reply_text(str(exc))
        return
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.exception("signals_handler failed to load signal")
        if update.message:
            await update.message.reply_text(f"Signal load failed: {exc}")
        return

    signal_id = payload.get("signal_id", "unknown")
    try:
        status_report = StatusAPI().load_latest_status()
    except Exception:
        status_report = {}
    approval_repo = ApprovalRepository(SQLiteStore())
    approval_state = approval_repo.get_signal_approval_status(signal_id)
    text = format_signal_card(
        payload,
        approval_status=approval_state["status"] or "未审批",
        approval_expires_at=approval_state["expires_at"],
        top_parameter_view=(status_report.get("top_parameter_view") if isinstance(status_report, dict) else None),
    )

    if update.message:
        try:
            chunks = split_markdown_message(text)
            for index, chunk in enumerate(chunks):
                await update.message.reply_text(
                    text=chunk,
                    parse_mode="Markdown",
                    reply_markup=build_signal_actions_keyboard(signal_id) if index == 0 else None,
                )
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.exception("signals_handler failed to send message")
            await update.message.reply_text(f"Signal render failed: {exc}")
