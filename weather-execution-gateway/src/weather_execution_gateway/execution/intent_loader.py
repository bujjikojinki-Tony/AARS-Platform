from __future__ import annotations

import json
from pathlib import Path

from weather_execution_gateway.models.order_intent import OrderIntent


class IntentLoader:
    def __init__(self, pending_dir: str = "data/outputs/pending_intents") -> None:
        self.pending_dir = Path(pending_dir)
        self.pending_dir.mkdir(parents=True, exist_ok=True)

    def list_pending_files(self) -> list[Path]:
        return sorted(self.pending_dir.glob("*.json"))

    def load_first_pending(self) -> OrderIntent | None:
        files = self.list_pending_files()
        if not files:
            return None

        payload = json.loads(files[0].read_text(encoding="utf-8"))
        return OrderIntent(**payload)

    def mark_consumed(self, path: Path) -> Path:
        consumed_dir = self.pending_dir.parent / "consumed_intents"
        consumed_dir.mkdir(parents=True, exist_ok=True)
        target = consumed_dir / path.name
        path.rename(target)
        return target
