from __future__ import annotations

from typing import Any

try:
    from telegram.ext import (
        Application,
        CallbackQueryHandler,
        CommandHandler,
        MessageHandler,
        filters,
    )
except ModuleNotFoundError:  # pragma: no cover - local offline test fallback
    Application = Any
    CallbackQueryHandler = Any
    CommandHandler = Any
    MessageHandler = Any
    filters = Any

from weather_telegram_console.bot.handlers.approvals import approval_callback_handler
from weather_telegram_console.bot.handlers.controls import kill_handler
from weather_telegram_console.bot.handlers.market import market_handler
from weather_telegram_console.bot.handlers.opportunities import opportunities_handler
from weather_telegram_console.bot.handlers.monitoring import monitoring_handler
from weather_telegram_console.bot.handlers.navigation import navigation_callback_handler
from weather_telegram_console.bot.handlers.text_commands import text_command_router
from weather_telegram_console.bot.handlers.ops_alerts import opsack_handler, opsqueue_handler
from weather_telegram_console.bot.handlers.signals import signals_handler
from weather_telegram_console.bot.handlers.start import start_handler
from weather_telegram_console.bot.handlers.status import status_handler
from weather_telegram_console.bot.handlers.timeline import timeline_handler
from weather_telegram_console.settings import (
    describe_telegram_network_settings,
    get_bot_token,
    get_telegram_api_base_url,
    get_telegram_get_updates_proxy,
    get_telegram_proxy,
)


async def error_handler(update: object, context: object) -> None:
    print(f"Unhandled error: {context}")
    exception = getattr(context, "error", None)
    if exception is not None:
        print(f"Unhandled exception detail: {exception!r}")


def build_app() -> Application:
    if Application is Any:
        raise RuntimeError("python-telegram-bot is not installed")
    builder = Application.builder().token(get_bot_token())

    base_url = get_telegram_api_base_url()
    if base_url:
        builder = builder.base_url(base_url)

    proxy = get_telegram_proxy()
    if proxy:
        builder = builder.proxy(proxy)

    updates_proxy = get_telegram_get_updates_proxy()
    if updates_proxy:
        builder = builder.get_updates_proxy(updates_proxy)

    application = builder.build()

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("status", status_handler))
    application.add_handler(CommandHandler("market", market_handler))
    application.add_handler(CommandHandler("opportunities", opportunities_handler))
    application.add_handler(CommandHandler("opportunity", opportunities_handler))
    application.add_handler(CommandHandler("monitoring", monitoring_handler))
    application.add_handler(CommandHandler("timeline", timeline_handler))
    application.add_handler(CommandHandler("signals", signals_handler))
    application.add_handler(CommandHandler("signal", signals_handler))
    application.add_handler(CommandHandler("kill", kill_handler))
    application.add_handler(CommandHandler("opsqueue", opsqueue_handler))
    application.add_handler(CommandHandler("opsack", opsack_handler))
    application.add_handler(CallbackQueryHandler(navigation_callback_handler, pattern=r"^nav:"))
    application.add_handler(CallbackQueryHandler(approval_callback_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_command_router))
    application.add_error_handler(error_handler)

    return application


def main() -> None:
    app = build_app()
    logger.info("Telegram network settings: %s", describe_telegram_network_settings())
    app.run_polling()
