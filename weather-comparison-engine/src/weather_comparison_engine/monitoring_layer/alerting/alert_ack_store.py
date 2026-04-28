from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass(slots=True)
class AlertAckStore:
    path: Path
    acknowledgements: dict[str, dict] = field(default_factory=dict)

    def load(self) -> dict[str, dict]:
        if self.path.exists():
            try:
                payload = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                payload = {}
            self.acknowledgements = payload if isinstance(payload, dict) else {}
        return self.acknowledgements

    def ack(self, key: str, *, acknowledged_by: str = "system", note: str = "") -> dict:
        self.acknowledgements[key] = {
            "acknowledged_at": datetime.now(timezone.utc).isoformat(),
            "acknowledged_by": acknowledged_by,
            "note": note,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.acknowledgements, indent=2, ensure_ascii=False), encoding="utf-8")
        return self.acknowledgements[key]
