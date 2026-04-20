from __future__ import annotations

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
from weather_telegram_console.integrations.signal_api import SignalAPI
from weather_telegram_console.storage.session_repo import ApprovalRepository
from weather_telegram_console.storage.sqlite import SQLiteStore


async def signals_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    signal_api = SignalAPI()

    try:
        payload = signal_api.load_latest_signal()
    except FileNotFoundError as exc:
        if update.message:
            await update.message.reply_text(str(exc))
        return

    signal_id = payload.get("signal_id", "unknown")
    approval_repo = ApprovalRepository(SQLiteStore())
    approval_state = approval_repo.get_signal_approval_status(signal_id)
    text = format_signal_card(
        payload,
        approval_status=approval_state["status"] or "未审批",
        approval_expires_at=approval_state["expires_at"],
    )

    if update.message:
        await update.message.reply_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=build_signal_actions_keyboard(signal_id),
        )
