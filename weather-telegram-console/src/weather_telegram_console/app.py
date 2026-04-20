from __future__ import annotations

from typing import Any

try:
    from telegram.ext import (
        Application,
        CallbackQueryHandler,
        CommandHandler,
    )
except ModuleNotFoundError:  # pragma: no cover - local offline test fallback
    Application = Any
    CallbackQueryHandler = Any
    CommandHandler = Any

from weather_telegram_console.bot.handlers.approvals import approval_callback_handler
from weather_telegram_console.bot.handlers.controls import kill_handler
from weather_telegram_console.bot.handlers.market import market_handler
from weather_telegram_console.bot.handlers.ops_alerts import opsack_handler, opsqueue_handler
from weather_telegram_console.bot.handlers.signals import signals_handler
from weather_telegram_console.bot.handlers.start import start_handler
from weather_telegram_console.bot.handlers.status import status_handler
from weather_telegram_console.bot.handlers.timeline import timeline_handler
from weather_telegram_console.settings import get_bot_token


async def error_handler(update: object, context: object) -> None:
    print(f"Unhandled error: {context}")


def build_app() -> Application:
    if Application is Any:
        raise RuntimeError("python-telegram-bot is not installed")
    application = Application.builder().token(get_bot_token()).build()

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("status", status_handler))
    application.add_handler(CommandHandler("market", market_handler))
    application.add_handler(CommandHandler("timeline", timeline_handler))
    application.add_handler(CommandHandler("signals", signals_handler))
    application.add_handler(CommandHandler("kill", kill_handler))
    application.add_handler(CommandHandler("opsqueue", opsqueue_handler))
    application.add_handler(CommandHandler("opsack", opsack_handler))
    application.add_handler(CallbackQueryHandler(approval_callback_handler))
    application.add_error_handler(error_handler)

    return application


def main() -> None:
    app = build_app()
    app.run_polling()
