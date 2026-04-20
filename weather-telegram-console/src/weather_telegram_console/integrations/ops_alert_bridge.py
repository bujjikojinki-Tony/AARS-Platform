from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_STATE_SCHEMA_VERSION = "ops_alert_bridge_state.v2"
_NOTIFICATION_SCHEMA_VERSION = "telegram_ops_notification.v1"
_DEFAULT_COOLDOWN_MINUTES = 30


def sync_ops_alerts_to_notification_queue(
    *,
    alerts_path: Path,
    state_path: Path,
    queue_path: Path,
    max_batch: int = 50,
) -> dict:
    alerts = _load_jsonl(alerts_path)
    state = _load_state(state_path)
    processed = set(str(item) for item in state.get("processed_keys") or [])
    dedupe_state = state.get("dedupe_state")
    if not isinstance(dedupe_state, dict):
        dedupe_state = {}

    queued = 0
    skipped = 0
    suppressed = 0
    for event in alerts:
        if queued >= max_batch:
            break
        dedupe_key = _event_dedupe_key(event)
        event_at = _parse_timestamp(event.get("event_at")) or datetime.now(timezone.utc)
        event_cooldown_until = _parse_timestamp(event.get("cooldown_until"))
        cooldown_minutes = _event_cooldown_minutes(event)
        cooldown_until = event_cooldown_until or (event_at + timedelta(minutes=cooldown_minutes))
        record = dedupe_state.get(dedupe_key)
        if isinstance(record, dict):
            existing_until = _parse_timestamp(record.get("cooldown_until"))
            if existing_until and event_at <= existing_until:
                record["delivery_state"] = "suppressed"
                record["suppressed_count"] = int(record.get("suppressed_count") or 0) + 1
                record["last_event_at"] = event.get("event_at")
                record["last_suppressed_at"] = datetime.now(timezone.utc).isoformat()
                record["cooldown_until"] = existing_until.isoformat()
                dedupe_state[dedupe_key] = record
                suppressed += 1
                skipped += 1
                continue
        if dedupe_key in processed:
            record = dedupe_state.get(dedupe_key)
            if isinstance(record, dict):
                existing_until = _parse_timestamp(record.get("cooldown_until"))
                if existing_until and event_at <= existing_until:
                    record["delivery_state"] = "suppressed"
                    record["suppressed_count"] = int(record.get("suppressed_count") or 0) + 1
                    record["last_event_at"] = event.get("event_at")
                    record["last_suppressed_at"] = datetime.now(timezone.utc).isoformat()
                    record["cooldown_until"] = existing_until.isoformat()
                    dedupe_state[dedupe_key] = record
                    suppressed += 1
                    skipped += 1
                    continue
            # Once cooldown expires, allow the alert to be enqueued again.
            processed.discard(dedupe_key)
        notification = _build_notification(
            event,
            dedupe_key=dedupe_key,
            cooldown_until=cooldown_until.isoformat(),
            cooldown_minutes=cooldown_minutes,
        )
        _append_jsonl(queue_path, notification)
        processed.add(dedupe_key)
        dedupe_state[dedupe_key] = {
            "dedupe_key": dedupe_key,
            "delivery_state": "pending",
            "last_event_at": event.get("event_at"),
            "last_sent_at": None,
            "last_suppressed_at": None,
            "suppressed_count": int((record or {}).get("suppressed_count") or 0) if isinstance(record, dict) else 0,
            "cooldown_until": cooldown_until.isoformat(),
        }
        queued += 1

    _write_state(state_path, processed, dedupe_state)
    return {
        "queued": queued,
        "skipped": skipped,
        "suppressed": suppressed,
        "total_alerts_seen": len(alerts),
        "queue_path": str(queue_path),
        "state_path": str(state_path),
    }


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except Exception:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": _STATE_SCHEMA_VERSION, "processed_keys": [], "dedupe_state": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"schema_version": _STATE_SCHEMA_VERSION, "processed_keys": [], "dedupe_state": {}}
    if not isinstance(payload, dict):
        return {"schema_version": _STATE_SCHEMA_VERSION, "processed_keys": [], "dedupe_state": {}}
    return {
        "schema_version": str(payload.get("schema_version") or _STATE_SCHEMA_VERSION),
        "processed_keys": [str(item) for item in payload.get("processed_keys") or []],
        "dedupe_state": payload.get("dedupe_state") if isinstance(payload.get("dedupe_state"), dict) else {},
    }


def _write_state(path: Path, processed_keys: set[str], dedupe_state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Keep bounded state size while preserving recent dedupe memory.
    keys = sorted(processed_keys)[-5000:]
    payload = {
        "schema_version": _STATE_SCHEMA_VERSION,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "processed_keys": keys,
        "dedupe_state": dedupe_state,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _event_dedupe_key(event: dict) -> str:
    explicit = str(event.get("event_id") or "").strip()
    if explicit:
        return explicit
    base = json.dumps(
        {
            "event_at": event.get("event_at"),
            "market_id": event.get("market_id"),
            "primary_block_reason": event.get("primary_block_reason"),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:24]


def _event_cooldown_minutes(event: dict) -> int:
    raw = event.get("cooldown_minutes") or event.get("cooldown_window_minutes")
    try:
        value = int(raw)
    except Exception:
        value = _DEFAULT_COOLDOWN_MINUTES
    return max(1, value)


def _build_notification(
    event: dict,
    *,
    dedupe_key: str,
    cooldown_until: str,
    cooldown_minutes: int,
) -> dict:
    severity = str(event.get("severity") or "high").upper()
    market_id = str(event.get("market_id") or "-")
    reason = str(event.get("primary_block_reason") or "-")
    action = str(event.get("recommended_operator_action") or "hold_execution_and_review")
    text = (
        f"[AARS OPS ALERT][{severity}] market={market_id} "
        f"reason={reason} action={action}"
    )
    return {
        "schema_version": _NOTIFICATION_SCHEMA_VERSION,
        "notification_id": f"ops_{dedupe_key}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
        "delivery_state": "pending",
        "channel": "telegram_ops_bridge",
        "dedupe_key": dedupe_key,
        "cooldown_minutes": cooldown_minutes,
        "cooldown_until": cooldown_until,
        "last_sent_at": None,
        "suppressed_count": int(event.get("suppressed_count") or 0),
        "text": text,
        "payload": {
            "event_type": event.get("event_type"),
            "event_at": event.get("event_at"),
            "severity": event.get("severity"),
            "market_id": event.get("market_id"),
            "primary_block_reason": event.get("primary_block_reason"),
            "recommended_operator_action": event.get("recommended_operator_action"),
            "block_reasons": event.get("block_reasons") or [],
            "cooldown_until": cooldown_until,
            "cooldown_minutes": cooldown_minutes,
        },
    }


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
