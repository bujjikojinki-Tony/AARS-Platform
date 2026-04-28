from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from weather_comparison_engine.settings import FAMILY_ANOMALY_SUMMARY_JSON


def route_family_anomaly_events(
    *,
    report: dict,
    output_path: Path | None = None,
    now: datetime | None = None,
) -> dict:
    timestamp = now or datetime.now(timezone.utc)
    out = output_path or FAMILY_ANOMALY_SUMMARY_JSON
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "output_path": str(out),
        "generated_at": timestamp.isoformat(),
        "top_anomalies": report.get("top_anomalies") or [],
        "family_count": report.get("family_count") or 0,
    }
