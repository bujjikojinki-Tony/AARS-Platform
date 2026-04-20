from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def list_pending_ops_notifications(*, queue_path: Path, max_batch: int = 20) -> list[dict]:
    notifications = _load_jsonl(queue_path)
    selected: list[dict] = []
    for item in notifications:
        if len(selected) >= max_batch:
            break
        if str(item.get("status") or "").lower() != "pending":
            continue
        if str(item.get("delivery_state") or "").lower() == "suppressed":
            continue
        if not str(item.get("notification_id") or "").strip():
            continue
        selected.append(item)
    return selected


def summarize_ops_notification_queue(*, queue_path: Path) -> dict:
    notifications = _load_jsonl(queue_path)
    counts = {"pending": 0, "sent": 0, "acked": 0, "suppressed": 0, "other": 0}
    for item in notifications:
        state = str(item.get("delivery_state") or item.get("status") or "").lower()
        if state in counts:
            counts[state] += 1
        else:
            counts["other"] += 1
    return {
        "queue_path": str(queue_path),
        "schema_version": "telegram_ops_queue_summary.v1",
        "notification_count": len(notifications),
        "delivery_state_counts": counts,
    }


def dispatch_ops_notifications(
    *,
    queue_path: Path,
    delivery_log_path: Path,
    max_batch: int = 20,
    dry_run: bool = False,
) -> dict:
    notifications = _load_jsonl(queue_path)
    now = datetime.now(timezone.utc).isoformat()
    dispatched_ids: list[str] = []
    updated = False

    for item in notifications:
        if len(dispatched_ids) >= max_batch:
            break
        if str(item.get("status") or "").lower() != "pending":
            continue
        notification_id = str(item.get("notification_id") or "")
        if not notification_id:
            continue
        dispatched_ids.append(notification_id)
        if dry_run:
            continue
        mark_sent_report = mark_ops_notification_sent(
            queue_path=queue_path,
            delivery_log_path=delivery_log_path,
            notification_id=notification_id,
            sent_by="dispatcher",
            sent_channel=str(item.get("channel") or "telegram_ops_bridge"),
            sent_metadata={},
        )
        if mark_sent_report.get("sent"):
            updated = True

    if updated:
        notifications = _load_jsonl(queue_path)

    return {
        "queue_path": str(queue_path),
        "delivery_log_path": str(delivery_log_path),
        "dispatched_count": len(dispatched_ids),
        "dispatched_notification_ids": dispatched_ids,
        "dry_run": dry_run,
        "queue_summary": summarize_ops_notification_queue(queue_path=queue_path),
    }


def mark_ops_notification_sent(
    *,
    queue_path: Path,
    delivery_log_path: Path,
    notification_id: str,
    sent_by: str = "dispatcher",
    sent_channel: str = "telegram_ops_bridge",
    sent_metadata: dict | None = None,
) -> dict:
    notifications = _load_jsonl(queue_path)
    target = str(notification_id or "").strip()
    if not target:
        return {"sent": False, "reason": "notification_id_empty"}

    now = datetime.now(timezone.utc).isoformat()
    found = False
    updated = False
    for item in notifications:
        if str(item.get("notification_id") or "") != target:
            continue
        found = True
        if str(item.get("status") or "").lower() == "sent":
            return {"sent": True, "already_sent": True, "notification_id": target}
        if str(item.get("status") or "").lower() == "acked":
            return {"sent": False, "reason": "already_acked", "notification_id": target}
        item["status"] = "sent"
        item["sent_at"] = now
        item["last_sent_at"] = now
        item["sent_by"] = sent_by
        item["sent_channel"] = sent_channel
        item["delivery_state"] = "sent"
        metadata = sent_metadata if isinstance(sent_metadata, dict) else {}
        if metadata:
            item["sent_metadata"] = metadata
        updated = True
        break

    if not found:
        return {"sent": False, "reason": "notification_not_found", "notification_id": target}

    if updated:
        _write_jsonl(queue_path, notifications)
        _append_jsonl(
            delivery_log_path,
            {
                "schema_version": "telegram_ops_delivery_event.v1",
                "event_at": now,
                "event_type": "notification_sent",
                "notification_id": target,
                "sent_by": sent_by,
                "channel": sent_channel,
                "sent_metadata": sent_metadata if isinstance(sent_metadata, dict) else {},
            },
        )

    return {
        "sent": True,
        "notification_id": target,
        "already_sent": False,
        "delivery_state": "sent",
        "queue_summary": summarize_ops_notification_queue(queue_path=queue_path),
    }


def ack_ops_notification(
    *,
    queue_path: Path,
    delivery_log_path: Path,
    notification_id: str,
    acked_by: str = "operator",
) -> dict:
    notifications = _load_jsonl(queue_path)
    target = str(notification_id or "").strip()
    if not target:
        return {"acked": False, "reason": "notification_id_empty"}

    now = datetime.now(timezone.utc).isoformat()
    found = False
    updated = False
    for item in notifications:
        if str(item.get("notification_id") or "") != target:
            continue
        found = True
        if str(item.get("status") or "").lower() == "acked":
            return {"acked": True, "already_acked": True, "notification_id": target}
        item["status"] = "acked"
        item["acked_at"] = now
        item["acked_by"] = acked_by
        item["delivery_state"] = "acked"
        updated = True
        break

    if not found:
        return {"acked": False, "reason": "notification_not_found", "notification_id": target}

    if updated:
        _write_jsonl(queue_path, notifications)
        _append_jsonl(
            delivery_log_path,
            {
                "schema_version": "telegram_ops_delivery_event.v1",
                "event_at": now,
                "event_type": "notification_acked",
                "notification_id": target,
                "acked_by": acked_by,
            },
        )

    return {
        "acked": True,
        "notification_id": target,
        "already_acked": False,
        "delivery_state": "acked",
        "queue_summary": summarize_ops_notification_queue(queue_path=queue_path),
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


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    path.write_text(content, encoding="utf-8")


def _append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload, ensure_ascii=False) + "\n")
