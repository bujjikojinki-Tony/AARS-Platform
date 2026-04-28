from __future__ import annotations

import json
from pathlib import Path

from weather_telegram_console.settings import (
    get_operations_monitor_summary_path,
    get_operations_monitor_view_path,
)


class OperationsMonitorAPI:
    def load_latest_operations_monitor(self) -> dict:
        payload = self._load_json(get_operations_monitor_view_path())
        if not isinstance(payload, dict) or not payload:
            raise FileNotFoundError("No operations monitor snapshot found yet.")
        summary = self._load_json(get_operations_monitor_summary_path())
        if summary:
            payload.setdefault("summary", summary)
        return payload

    def _load_json(self, path: Path) -> dict:
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return payload if isinstance(payload, dict) else {}
