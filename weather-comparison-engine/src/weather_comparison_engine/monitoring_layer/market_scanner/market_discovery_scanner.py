from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from weather_comparison_engine.settings import (
    ALERTS_OUTPUT_DIR,
    MARKET_UNIVERSE_SNAPSHOT_JSON,
    OPPORTUNITY_BOARD_CANONICAL_VIEW_JSON,
    OPPORTUNITY_SEED_LIST_JSON,
    OUTPUT_DIR,
)


def build_market_universe_snapshot(
    *,
    opportunity_seed_path: Path | None = None,
    opportunity_board_path: Path | None = None,
    latest_dashboard_rows_path: Path | None = None,
    market_realtime_path: Path | None = None,
    watchlist_path: Path | None = None,
    now: datetime | None = None,
) -> dict:
    timestamp = now or datetime.now(timezone.utc)
    markets_by_id: dict[str, dict[str, Any]] = {}
    source_refs: dict[str, list[str]] = defaultdict(list)

    for source_name, rows in (
        ("seed", _load_seed_rows(opportunity_seed_path or OPPORTUNITY_SEED_LIST_JSON)),
        ("opportunity_board", _load_board_rows(opportunity_board_path or OPPORTUNITY_BOARD_CANONICAL_VIEW_JSON)),
        ("latest_dashboard_rows", _load_latest_dashboard_rows(latest_dashboard_rows_path)),
        ("watchlist", _load_watchlist_rows(watchlist_path)),
        ("market_realtime", _load_market_rows(market_realtime_path)),
    ):
        for row in rows:
            if not isinstance(row, dict):
                continue
            market_id = str(row.get("market_id") or row.get("row_id") or row.get("seed_id") or "").strip()
            if not market_id:
                continue
            existing = markets_by_id.setdefault(
                market_id,
                {
                    "schema_version": "market_universe_market.v1",
                    "market_id": market_id,
                    "question": row.get("question") or row.get("market_question") or row.get("title") or "-",
                    "city": row.get("city") or row.get("location_name") or "-",
                    "country": row.get("country") or row.get("location_country") or "-",
                    "market_family": row.get("market_family") or row.get("family") or "-",
                    "target_date": row.get("target_date") or row.get("date") or "-",
                    "band_scheme": row.get("band_scheme") or row.get("market_band_scheme") or "-",
                    "active_status": str(row.get("active_status") or row.get("active") or "active"),
                    "liquidity_score": _to_float(row.get("liquidity_score") or row.get("liquidity") or row.get("volume_24hr") or row.get("volume")) or 0.0,
                    "spread": _to_float(row.get("spread")) or 0.0,
                    "scan_priority": _merge_priority(
                        _source_priority(source_name),
                        row.get("scan_priority") or row.get("priority_level"),
                    ),
                    "freshness_status": _derive_freshness_status(source_name, row),
                    "freshness_reason": _derive_freshness_reason(source_name, row),
                    "seeded_from_opportunity_seed": source_name == "seed",
                    "upstream_refs": _build_upstream_refs(row, source_name),
                },
            )
            existing["seeded_from_opportunity_seed"] = existing["seeded_from_opportunity_seed"] or source_name == "seed"
            existing["scan_priority"] = _merge_priority(existing["scan_priority"], row.get("scan_priority") or row.get("priority_level"))
            existing["liquidity_score"] = max(existing["liquidity_score"], _to_float(row.get("liquidity_score") or row.get("liquidity") or row.get("volume_24hr") or row.get("volume")) or 0.0)
            existing["spread"] = min(existing["spread"], _to_float(row.get("spread")) if _to_float(row.get("spread")) is not None else existing["spread"])
            if _priority_rank(_source_priority(source_name)) < _priority_rank(str(existing.get("scan_priority") or "medium")):
                existing["scan_priority"] = _source_priority(source_name)
            if existing.get("freshness_status") in (None, "", "unknown") or _freshness_rank(_derive_freshness_status(source_name, row)) < _freshness_rank(str(existing.get("freshness_status") or "unknown")):
                existing["freshness_status"] = _derive_freshness_status(source_name, row)
                existing["freshness_reason"] = _derive_freshness_reason(source_name, row)
            _append_source_ref(source_refs, market_id, source_name)

    markets = sorted(
        markets_by_id.values(),
        key=lambda item: (
            _priority_rank(str(item.get("scan_priority") or "medium")),
            -(item.get("liquidity_score") or 0.0),
            float(item.get("spread") or 0.0),
            str(item.get("city") or ""),
            str(item.get("market_family") or ""),
        ),
    )
    for market in markets:
        market["upstream_refs"] = {
            **(market.get("upstream_refs") or {}),
            "source_refs": source_refs.get(str(market.get("market_id") or ""), []),
        }
    return {
        "schema_version": "market_universe_snapshot.v1",
        "generated_at": timestamp.isoformat(),
        "market_count": len(markets),
        "markets": markets,
        "source_refs": {
            "opportunity_seed_path": str(opportunity_seed_path or OPPORTUNITY_SEED_LIST_JSON),
            "opportunity_board_path": str(opportunity_board_path or OPPORTUNITY_BOARD_CANONICAL_VIEW_JSON),
            "latest_dashboard_rows_path": str(latest_dashboard_rows_path or OUTPUT_DIR / "latest_dashboard_rows.json"),
            "market_realtime_path": str(market_realtime_path or ""),
            "watchlist_path": str(watchlist_path or ""),
        },
    }


def write_market_universe_snapshot(path: Path | None, snapshot: dict) -> Path:
    out = path or MARKET_UNIVERSE_SNAPSHOT_JSON
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def _load_seed_rows(path: Path) -> list[dict]:
    payload = _load_json(path)
    rows = payload.get("rows") if isinstance(payload, dict) else []
    return rows if isinstance(rows, list) else []


def _load_board_rows(path: Path) -> list[dict]:
    payload = _load_json(path)
    rows = payload.get("rows") if isinstance(payload, dict) else []
    return rows if isinstance(rows, list) else []


def _load_latest_dashboard_rows(path: Path | None) -> list[dict]:
    if path is None:
        return []
    payload = _load_json(path)
    return payload if isinstance(payload, list) else []


def _load_watchlist_rows(path: Path | None) -> list[dict]:
    if path is None or not path.exists():
        return []
    payload = _load_json(path)
    if isinstance(payload, dict):
        rows = payload.get("rows") or payload.get("markets") or []
        return rows if isinstance(rows, list) else []
    return payload if isinstance(payload, list) else []


def _load_market_rows(path: Path | None) -> list[dict]:
    if path is None or not path.exists():
        return []
    payload = _load_json(path)
    if isinstance(payload, dict):
        if "markets" in payload and isinstance(payload["markets"], list):
            return payload["markets"]
        return [payload]
    return payload if isinstance(payload, list) else []


def _load_json(path: Path | None) -> dict | list:
    if path is None or not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _build_upstream_refs(row: dict, source_name: str) -> dict:
    return {
        "source_name": source_name,
        "market_id": row.get("market_id") or row.get("seed_id") or row.get("row_id") or "-",
        "comparison_ref": row.get("comparison_ref") or row.get("comparison_point_ref") or "-",
        "alert_ref": row.get("alert_ref") or "-",
        "anomaly_ref": row.get("anomaly_ref") or "-",
        "gate_ref": row.get("gate_ref") or "-",
    }


def _append_source_ref(source_refs: dict[str, list[str]], market_id: str, source_name: str) -> None:
    refs = source_refs[market_id]
    if source_name not in refs:
        refs.append(source_name)


def _merge_priority(current: str, new: object) -> str:
    if new in (None, ""):
        return current
    if _priority_rank(str(new)) < _priority_rank(current):
        return str(new)
    return current


def _priority_rank(priority: str) -> int:
    return {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(priority.lower(), 2)


def _source_priority(source_name: str) -> str:
    return {
        "market_realtime": "critical",
        "latest_dashboard_rows": "high",
        "opportunity_board": "high",
        "watchlist": "medium",
        "seed": "medium",
    }.get(source_name, "medium")


def _freshness_rank(status: str) -> int:
    return {"fresh": 0, "stale": 1, "unavailable": 2, "unknown": 3}.get(status.lower(), 3)


def _derive_freshness_status(source_name: str, row: dict) -> str:
    explicit = str(row.get("freshness_status") or row.get("scan_freshness_status") or "").lower()
    if explicit in {"fresh", "stale", "unavailable"}:
        return explicit
    if source_name in {"market_realtime", "latest_dashboard_rows", "opportunity_board"}:
        return "fresh"
    if source_name in {"watchlist", "seed"}:
        return "stale"
    return "unknown"


def _derive_freshness_reason(source_name: str, row: dict) -> str:
    explicit = row.get("freshness_reason") or row.get("scan_freshness_reason")
    if explicit:
        return str(explicit)
    if source_name == "market_realtime":
        return "realtime market snapshot"
    if source_name == "latest_dashboard_rows":
        return "latest dashboard row"
    if source_name == "opportunity_board":
        return "opportunity board row"
    if source_name == "watchlist":
        return "watchlist candidate"
    if source_name == "seed":
        return "manual seed prior"
    return "unknown source freshness"


def _to_float(value: object) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
