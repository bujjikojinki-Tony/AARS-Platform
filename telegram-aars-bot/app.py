import logging

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from config import TELEGRAM_BOT_TOKEN
from bot_handlers import (
    start,
    help_command,
    projects_command,
    use_project_command,
    new_project,
    status,
    spawn,
    run_step,
    review,
    stable_view,
    closure,
    stop,
    button_router,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


async def error_handler(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)


def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("projects", projects_command))
    application.add_handler(CommandHandler("use_project", use_project_command))
    application.add_handler(CommandHandler("new_project", new_project))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("spawn", spawn))
    application.add_handler(CommandHandler("run", run_step))
    application.add_handler(CommandHandler("review", review))
    application.add_handler(CommandHandler("stable_view", stable_view))
    application.add_handler(CommandHandler("closure", closure))
    application.add_handler(CommandHandler("stop", stop))

    application.add_handler(CallbackQueryHandler(button_router))
    application.add_error_handler(error_handler)

    print("AARS Telegram Bot is running...")
    application.run_polling()


if __name__ == "__main__":
    main()
