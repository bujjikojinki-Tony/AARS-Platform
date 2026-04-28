from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class MonitoringStatusBuilder:
    def __init__(self, *, now: datetime | None = None) -> None:
        self.now = now or datetime.now(timezone.utc)

    def build(self, worker_specs: list[dict]) -> dict:
        workers = [self._build_worker_status(spec) for spec in worker_specs]
        counts = _count_statuses(workers)
        return {
            "schema_version": "monitoring_status.v1",
            "generated_at": self.now.isoformat(),
            "overall_status": _overall_status(counts),
            "counts": counts,
            "workers": workers,
        }

    def write(self, path: str | Path, worker_specs: list[dict]) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(self.build(worker_specs), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return out

    def _build_worker_status(self, spec: dict) -> dict:
        path = Path(spec["path"])
        payload = _load_json(path)
        parsed_timestamp = _extract_timestamp(payload)
        payload_status = _extract_status(payload)
        if not path.exists():
            return {
                "worker": spec["worker"],
                "label": spec.get("label") or spec["worker"],
                "layer": spec.get("layer") or spec["worker"],
                "path": str(path),
                "status": "missing",
                "source_status": "missing",
                "last_success_at": None,
                "freshness_seconds": None,
                "stale_after_seconds": spec["stale_after_seconds"],
                "last_error": f"missing_file:{path}",
            }

        last_success_at = parsed_timestamp or _file_mtime(path)
        freshness_seconds = max((self.now - last_success_at).total_seconds(), 0.0)
        if payload_status == "blocked":
            status = "blocked"
            source_status = "blocked"
        elif parsed_timestamp is None:
            status = "warning"
            source_status = "unknown_timestamp"
        elif freshness_seconds > float(spec["stale_after_seconds"]):
            status = "stale"
            source_status = "stale"
        elif payload_status == "warning":
            status = "warning"
            source_status = "warning"
        else:
            status = "healthy"
            source_status = "ok"

        return {
            "worker": spec["worker"],
            "label": spec.get("label") or spec["worker"],
            "layer": spec.get("layer") or spec["worker"],
            "path": str(path),
            "status": status,
            "source_status": source_status,
            "last_success_at": last_success_at.isoformat(),
            "freshness_seconds": freshness_seconds,
            "stale_after_seconds": spec["stale_after_seconds"],
            "last_error": None,
        }


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _extract_timestamp(payload: Any) -> datetime | None:
    if isinstance(payload, dict):
        for key in ["updated_at", "timestamp", "generated_at", "created_at", "computed_at"]:
            parsed = _parse_iso(payload.get(key))
            if parsed is not None:
                return parsed
    if isinstance(payload, list):
        parsed_rows = [
            _parse_iso(item.get("timestamp"))
            for item in payload
            if isinstance(item, dict)
        ]
        parsed_rows = [row for row in parsed_rows if row is not None]
        if parsed_rows:
            return max(parsed_rows)
    return None


def _parse_iso(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _file_mtime(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def _count_statuses(workers: list[dict]) -> dict[str, int]:
    counts = {"healthy": 0, "warning": 0, "stale": 0, "missing": 0, "blocked": 0}
    for worker in workers:
        status = str(worker.get("status") or "warning")
        counts[status] = counts.get(status, 0) + 1
    return counts


def _overall_status(counts: dict[str, int]) -> str:
    if counts.get("missing", 0) > 0 or counts.get("stale", 0) > 0 or counts.get("blocked", 0) > 0:
        return "degraded"
    if counts.get("warning", 0) > 0:
        return "warning"
    return "healthy"


def _extract_status(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    for key in ("status", "overall_status"):
        status = payload.get(key)
        if isinstance(status, str) and status in {"healthy", "warning", "blocked", "degraded", "missing"}:
            if status == "degraded":
                return "warning"
            if status == "missing":
                return "blocked"
            return status
    return None
