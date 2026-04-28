from __future__ import annotations

import json
from pathlib import Path


class OpportunityBoardLoader:
    def load(self, path: str | Path) -> dict:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
