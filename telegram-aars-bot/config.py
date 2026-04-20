from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values


ROOT_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = ROOT_DIR.parent
WEATHER_CONSOLE_ENV_PATH = WORKSPACE_DIR / "weather-telegram-console" / ".env"
LOCAL_ENV_PATH = ROOT_DIR / ".env"


def _seed_env_from(path: Path) -> None:
    if not path.exists():
        return

    for key, value in dotenv_values(path).items():
        if value is None:
            continue
        os.environ.setdefault(key, value)


_seed_env_from(WEATHER_CONSOLE_ENV_PATH)
_seed_env_from(LOCAL_ENV_PATH)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("未找到 TELEGRAM_BOT_TOKEN，请检查 console/.env 或本地 .env 文件")
