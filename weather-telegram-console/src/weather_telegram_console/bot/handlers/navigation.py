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
from weather_telegram_console.bot.formatters.opportunity_board_card import format_opportunity_board_card
from weather_telegram_console.bot.formatters.monitoring_card import format_monitoring_card
from weather_telegram_console.bot.formatters.signal_card import format_signal_card
from weather_telegram_console.bot.formatters.status_card import format_status_card
from weather_telegram_console.bot.keyboards.signal_actions import build_signal_actions_keyboard
from weather_telegram_console.integrations.market_api import MarketAPI
from weather_telegram_console.integrations.opportunity_api import OpportunityAPI
from weather_telegram_console.integrations.monitoring_api import MonitoringAPI
from weather_telegram_console.integrations.signal_api import SignalAPI
from weather_telegram_console.integrations.status_api import StatusAPI
from weather_telegram_console.storage.session_repo import ApprovalRepository
from weather_telegram_console.storage.sqlite import SQLiteStore

logger = logging.getLogger(__name__)


async def navigation_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return

    logger.info("navigation_callback_handler invoked: %s", query.data or "")
    await query.answer()
    data = query.data or ""
    if not data.startswith("nav:"):
        return

    target = data.split(":", 1)[1]
    if target == "status":
        try:
            report = StatusAPI().load_latest_status()
            await query.edit_message_text(text=format_status_card(report), parse_mode="Markdown")
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.exception("navigation status failed")
            await query.edit_message_text(text=f"Status render failed: {exc}")
        return

    if target == "market":
        try:
            payload = MarketAPI().load_market_summary()
            await query.edit_message_text(text=format_market_card(payload), parse_mode="Markdown")
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.exception("navigation market failed")
            await query.edit_message_text(text=f"Market render failed: {exc}")
        return

    if target == "opportunities":
        try:
            payload = OpportunityAPI().load_opportunity_board()
            await query.edit_message_text(text=format_opportunity_board_card(payload), parse_mode="Markdown")
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.exception("navigation opportunities failed")
            await query.edit_message_text(text=f"Opportunity render failed: {exc}")
        return

    if target == "signals":
        try:
            payload = SignalAPI().load_latest_signal()
        except FileNotFoundError as exc:
            await query.edit_message_text(text=str(exc), parse_mode="Markdown")
            return
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.exception("navigation signals failed to load")
            await query.edit_message_text(text=f"Signal load failed: {exc}")
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
        try:
            await query.edit_message_text(
                text=text,
                parse_mode="Markdown",
                reply_markup=build_signal_actions_keyboard(signal_id),
            )
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.exception("navigation signals failed to render")
            await query.edit_message_text(text=f"Signal render failed: {exc}")
        return

    if target == "monitoring":
        try:
            payload = MonitoringAPI().load_latest_monitoring_signals()
            await query.edit_message_text(text=format_monitoring_card(payload), parse_mode="Markdown")
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.exception("navigation monitoring failed")
            await query.edit_message_text(text=f"Monitoring render failed: {exc}")
        return

    await query.edit_message_text(text=f"Unknown navigation action `{data}`.", parse_mode="Markdown")
