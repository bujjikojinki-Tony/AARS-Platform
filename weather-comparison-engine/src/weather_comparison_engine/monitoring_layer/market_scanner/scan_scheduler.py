from __future__ import annotations

from datetime import datetime, timezone


def build_scan_status(
    *,
    market_universe_snapshot: dict | None = None,
    evidence_scan_snapshot: dict | None = None,
    alert_events: list[dict] | None = None,
    now: datetime | None = None,
) -> dict:
    timestamp = now or datetime.now(timezone.utc)
    universe = market_universe_snapshot if isinstance(market_universe_snapshot, dict) else {}
    evidence = evidence_scan_snapshot if isinstance(evidence_scan_snapshot, dict) else {}
    rows = evidence.get("rows") if isinstance(evidence.get("rows"), list) else []
    alerts = [item for item in (alert_events or []) if isinstance(item, dict)]
    markets = universe.get("markets") if isinstance(universe.get("markets"), list) else []
    priority_counts = _count_by_key(markets, "scan_priority")
    freshness_counts = _count_by_key(rows, "freshness_status")
    fresh_count = sum(1 for row in rows if str(row.get("freshness_status") or "").lower() == "fresh")
    stale_count = sum(1 for row in rows if str(row.get("freshness_status") or "").lower() == "stale")
    unavailable_count = sum(1 for row in rows if str(row.get("freshness_status") or "").lower() == "unavailable")
    backlog_count = max(0, int(universe.get("market_count") or len(universe.get("markets") or [])) - len(rows))
    return {
        "schema_version": "scanner_status.v1",
        "generated_at": timestamp.isoformat(),
        "total_markets": int(universe.get("market_count") or len(universe.get("markets") or [])),
        "scanned_markets": len(rows),
        "fresh_markets": fresh_count,
        "stale_markets": stale_count,
        "unavailable_markets": unavailable_count,
        "alert_markets": len(alerts),
        "backlog_count": backlog_count,
        "next_scan_eta": _next_scan_eta(stale_count, unavailable_count, backlog_count),
        "priority_counts": priority_counts,
        "freshness_counts": freshness_counts,
        "summary": {
            "universe_version": universe.get("schema_version") or "-",
            "evidence_version": evidence.get("schema_version") or "-",
            "alert_count": len(alerts),
            "fresh_ratio": round(fresh_count / len(rows), 4) if rows else 0.0,
            "priority_mix": priority_counts,
            "freshness_mix": freshness_counts,
        },
    }


def _next_scan_eta(stale_count: int, unavailable_count: int, backlog_count: int) -> str:
    if unavailable_count > 0:
        return "1m"
    if stale_count > 0 or backlog_count > 0:
        return "5m"
    return "15m"


def _count_by_key(rows: list[dict], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        value = str(row.get(key) or "unknown").lower()
        counts[value] = counts.get(value, 0) + 1
    return counts
