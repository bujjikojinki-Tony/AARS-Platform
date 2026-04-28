from __future__ import annotations

import json
from pathlib import Path

from weather_comparison_engine.settings import SCANNER_STATUS_JSON


def write_scanner_status(path: Path | None, status: dict) -> Path:
    out = path or SCANNER_STATUS_JSON
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    return out
