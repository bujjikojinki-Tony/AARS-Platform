from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from weather_comparison_engine.settings import SCANNER_OPS_ALERTS_JSON


def route_scanner_ops_alerts(
    *,
    alerts: list[dict],
    output_path: Path | None = None,
    now: datetime | None = None,
) -> dict:
    timestamp = now or datetime.now(timezone.utc)
    out = output_path or SCANNER_OPS_ALERTS_JSON
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as fp:
        for alert in alerts:
            if isinstance(alert, dict):
                fp.write(json.dumps(alert, ensure_ascii=False) + "\n")
    return {
        "output_path": str(out),
        "generated_at": timestamp.isoformat(),
        "alert_count": len([alert for alert in alerts if isinstance(alert, dict)]),
    }
