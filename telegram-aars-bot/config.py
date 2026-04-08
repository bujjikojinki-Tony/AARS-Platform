import os

from dotenv import load_dotenv


load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("未找到 TELEGRAM_BOT_TOKEN，请检查 .env 文件")
