from telegram.ext import Application, CommandHandler

from bot_handlers import (
    closure,
    help_command,
    new_project,
    review,
    run_step,
    stable_view,
    spawn,
    start,
    status,
    stop,
)
from config import TELEGRAM_BOT_TOKEN


def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("new_project", new_project))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("spawn", spawn))
    application.add_handler(CommandHandler("run", run_step))
    application.add_handler(CommandHandler("review", review))
    application.add_handler(CommandHandler("stable_view", stable_view))
    application.add_handler(CommandHandler("closure", closure))
    application.add_handler(CommandHandler("stop", stop))

    print("AARS Telegram Bot is running...")
    application.run_polling()


if __name__ == "__main__":
    main()
