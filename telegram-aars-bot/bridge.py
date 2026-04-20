from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
WEATHER_CONSOLE_SRC = ROOT_DIR.parent / "weather-telegram-console" / "src"
if WEATHER_CONSOLE_SRC.exists():
    sys.path.insert(0, str(WEATHER_CONSOLE_SRC))

# Importing config seeds TELEGRAM_BOT_TOKEN from the weather console .env first,
# then falls back to this repo's .env. That keeps one operational source of truth.
import config  # noqa: F401
from weather_telegram_console.app import build_app as build_weather_console_app

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def build_bridged_app():
    return build_weather_console_app()


def main() -> None:
    application = build_bridged_app()
    logger.info("telegram-aars-bot is bridged to weather-telegram-console")
    application.run_polling()
