from __future__ import annotations

import json
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path


def should_emit_ops_alert(summary: dict, *, exit_code: int) -> bool:
    if exit_code == 0:
        return False
    return str(summary.get("automation_signal") or "").strip().lower() == "red"


def build_ops_alert_event(
    *,
    summary: dict,
    fail_on_signal: str,
    exit_code: int,
    cycle: int | None = None,
    now: datetime | None = None,
) -> dict:
    timestamp = now or datetime.now(timezone.utc)
    cooldown_minutes = _cooldown_minutes(summary)
    dedupe_key = _dedupe_key(summary)
    return {
        "schema_version": "gate_stack_ops_alert.v1",
        "event_at": timestamp.isoformat(),
        "event_type": "gate_stack_runtime_alert",
        "severity": str(summary.get("severity") or "high"),
        "automation_signal": str(summary.get("automation_signal") or "red"),
        "exit_code": int(exit_code),
        "fail_on_signal": str(fail_on_signal),
        "market_id": summary.get("market_id"),
        "primary_block_reason": summary.get("primary_block_reason"),
        "recommended_operator_action": summary.get("recommended_operator_action"),
        "block_reasons": [str(item) for item in summary.get("block_reasons") or []],
        "gate_source": str(summary.get("gate_source") or "api"),
        "cycle": cycle,
        "source_schema_version": str(summary.get("source_schema_version") or "unknown"),
        "dedupe_key": dedupe_key,
        "cooldown_minutes": cooldown_minutes,
        "cooldown_until": (timestamp + timedelta(minutes=cooldown_minutes)).isoformat(),
        "last_sent_at": None,
        "suppressed_count": 0,
        "delivery_state": "pending",
    }


def append_ops_alert(path: str | Path, event: dict) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(event, ensure_ascii=False) + "\n")
    return out


def _cooldown_minutes(summary: dict) -> int:
    raw = summary.get("cooldown_minutes")
    try:
        value = int(raw)
    except Exception:
        value = 30
    return max(1, value)


def _dedupe_key(summary: dict) -> str:
    base = json.dumps(
        {
            "market_id": summary.get("market_id"),
            "primary_block_reason": summary.get("primary_block_reason"),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:24]
