from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from weather_telegram_console.settings import get_signal_json_path


class SignalAPI:
    def load_latest_signal(self) -> dict:
        path: Path = get_signal_json_path()
        if not path.exists():
            raise FileNotFoundError(f"Signal file not found: {path}")
        return json.loads(path.read_text(encoding="utf-8"))


class SignalApiClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or "").rstrip("/")

    async def get_latest_signal(self) -> dict[str, Any]:
        return SignalAPI().load_latest_signal()
