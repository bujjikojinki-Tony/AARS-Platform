from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from weather_comparison_engine.settings import ALERTS_OUTPUT_DIR, MARKET_ALERT_EVENTS_JSON, SCAN_QUEUE_STATUS_JSON

from .alert_deduper import AlertDeduper


def route_market_alert_events(
    *,
    events: list[dict],
    output_path: Path | None = None,
    queue_status_path: Path | None = None,
    now: datetime | None = None,
) -> dict:
    timestamp = now or datetime.now(timezone.utc)
    out = output_path or MARKET_ALERT_EVENTS_JSON
    queue_path = queue_status_path or SCAN_QUEUE_STATUS_JSON
    deduper = AlertDeduper()
    accepted: list[dict] = []
    suppressed: list[dict] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        severity = str(event.get("severity") or "watch").lower()
        dedupe_key = _dedupe_key(event)
        if deduper.should_emit(dedupe_key=dedupe_key, severity=severity, now=timestamp):
            accepted.append(event)
        else:
            suppressed.append(event)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as fp:
        for event in accepted:
            fp.write(json.dumps(event, ensure_ascii=False) + "\n")
    queue_status = {
        "schema_version": "alert_queue_status.v1",
        "generated_at": timestamp.isoformat(),
        "accepted_count": len(accepted),
        "suppressed_count": len(suppressed),
        "output_path": str(out),
        "alerts_output_dir": str(ALERTS_OUTPUT_DIR),
    }
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue_path.write_text(json.dumps(queue_status, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"output_path": str(out), "queue_status_path": str(queue_path), "accepted": accepted, "suppressed": suppressed}


def _dedupe_key(event: dict) -> str:
    return "|".join(
        str(event.get(key) or "-")
        for key in ("market_id", "event_type", "primary_reason")
    )
