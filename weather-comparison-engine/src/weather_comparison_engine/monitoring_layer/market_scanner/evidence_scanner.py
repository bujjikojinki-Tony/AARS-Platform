from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from weather_comparison_engine.settings import (
    EVIDENCE_SCAN_SNAPSHOT_JSON,
    MARKET_ALERT_EVENTS_DIR,
    MARKET_ANOMALY_EVENTS_DIR,
    MARKET_UNIVERSE_SNAPSHOT_JSON,
)


def build_evidence_scan_snapshot(
    *,
    market_universe_snapshot: dict | None = None,
    market_alert_events_dir: Path | None = None,
    market_anomaly_events_dir: Path | None = None,
    now: datetime | None = None,
) -> dict:
    timestamp = now or datetime.now(timezone.utc)
    universe = market_universe_snapshot if isinstance(market_universe_snapshot, dict) else _load_json(MARKET_UNIVERSE_SNAPSHOT_JSON)
    markets = universe.get("markets") if isinstance(universe.get("markets"), list) else []
    alert_dir = market_alert_events_dir or MARKET_ALERT_EVENTS_DIR
    anomaly_dir = market_anomaly_events_dir or MARKET_ANOMALY_EVENTS_DIR
    latest_alerts = _load_latest_json_records(alert_dir)
    latest_anomalies = _load_latest_json_records(anomaly_dir)

    rows: list[dict] = []
    for market in markets:
        if not isinstance(market, dict):
            continue
        market_id = str(market.get("market_id") or "").strip()
        if not market_id:
            continue
        latest_alert = _latest_for_market(latest_alerts, market_id)
        latest_anomaly = _latest_for_market(latest_anomalies, market_id)
        freshness_status = _derive_freshness_status(market, latest_alert, latest_anomaly)
        freshness_reason = _derive_freshness_reason(market, latest_alert, latest_anomaly)
        rows.append(
            {
                "schema_version": "evidence_scan_row.v1",
                "market_id": market_id,
                "market_family": market.get("market_family") or "-",
                "city": market.get("city") or "-",
                "scan_priority": market.get("scan_priority") or "medium",
                "forecast_snapshot_ref": latest_alert.get("contract_refs", {}).get("forecast_snapshot_ref") or "-",
                "observation_snapshot_ref": latest_alert.get("contract_refs", {}).get("observation_snapshot_ref") or "-",
                "comparison_point_ref": latest_alert.get("contract_refs", {}).get("comparison_point_ref") or "-",
                "source_precision_score": _source_precision_score(market, latest_alert, latest_anomaly),
                "freshness_status": freshness_status,
                "freshness_reason": freshness_reason,
                "best_model": market.get("best_model") or latest_alert.get("best_model") or "-",
                "best_source_stack": market.get("best_source_stack") or [],
                "scan_status": _scan_status(freshness_status, latest_alert, latest_anomaly),
                "latest_alert_severity": latest_alert.get("severity") or "-",
                "latest_anomaly_score": latest_anomaly.get("anomaly_score") or 0.0,
                "generated_at": timestamp.isoformat(),
                "upstream_refs": {
                    "market_universe_ref": universe.get("generated_at") or "-",
                    "market_alert_ref": latest_alert.get("event_id") or "-",
                    "market_anomaly_ref": latest_anomaly.get("event_id") or "-",
                },
            }
        )

    summary = {
        "schema_version": "evidence_scan_snapshot.v1",
        "generated_at": timestamp.isoformat(),
        "market_count": len(rows),
        "fresh_count": sum(1 for row in rows if str(row.get("freshness_status") or "").lower() == "fresh"),
        "stale_count": sum(1 for row in rows if str(row.get("freshness_status") or "").lower() == "stale"),
        "unavailable_count": sum(1 for row in rows if str(row.get("freshness_status") or "").lower() == "unavailable"),
        "rows": rows,
        "source_refs": {
            "market_universe_snapshot": str(MARKET_UNIVERSE_SNAPSHOT_JSON),
            "market_alert_events_dir": str(alert_dir),
            "market_anomaly_events_dir": str(anomaly_dir),
        },
    }
    return summary


def write_evidence_scan_snapshot(path: Path | None, snapshot: dict) -> Path:
    out = path or EVIDENCE_SCAN_SNAPSHOT_JSON
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def _latest_for_market(records: list[dict], market_id: str) -> dict:
    candidates = [row for row in records if str(row.get("market_id") or "") == market_id]
    if not candidates:
        return {}
    return candidates[-1]


def _load_latest_json_records(directory: Path) -> list[dict]:
    if not directory.exists():
        return []
    records: list[dict] = []
    for path in sorted(directory.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(payload, dict):
            records.append(payload)
    for path in sorted(directory.glob("*.jsonl")):
        try:
            lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        except Exception:
            continue
        for line in lines:
            try:
                payload = json.loads(line)
            except Exception:
                continue
            if isinstance(payload, dict):
                records.append(payload)
    return records


def _source_precision_score(market: dict, alert: dict, anomaly: dict) -> float:
    score = 0.0
    if str(market.get("seeded_from_opportunity_seed")) == "True":
        score += 0.1
    if str(alert.get("source_match_grade") or market.get("source_match_grade") or "").lower() == "exact_station":
        score += 0.4
    elif str(alert.get("source_match_grade") or market.get("source_match_grade") or "").lower() == "family_only":
        score += 0.2
    if str(alert.get("freshness_status") or market.get("freshness_status") or "").lower() == "fresh":
        score += 0.3
    if float(anomaly.get("anomaly_score") or 0.0) < 0.5:
        score += 0.2
    return round(min(1.0, score), 4)


def _scan_status(freshness_status: str, alert: dict, anomaly: dict) -> str:
    if str(freshness_status).lower() == "unavailable":
        return "blocked"
    if str(freshness_status).lower() == "unknown":
        return "degraded"
    if float(alert.get("alert_score") or 0.0) >= 0.8 or float(anomaly.get("anomaly_score") or 0.0) >= 0.8:
        return "alerted"
    if str(freshness_status).lower() == "stale":
        return "degraded"
    return "healthy"


def _derive_freshness_status(market: dict, alert: dict, anomaly: dict) -> str:
    for candidate in (
        market.get("freshness_status"),
        alert.get("freshness_status"),
        anomaly.get("freshness_status"),
    ):
        status = str(candidate or "").lower()
        if status in {"fresh", "stale", "unavailable"}:
            return status
    source_refs = market.get("upstream_refs", {}).get("source_refs") or []
    if "market_realtime" in source_refs or "latest_dashboard_rows" in source_refs:
        return "fresh"
    if "opportunity_board" in source_refs or "watchlist" in source_refs or "seed" in source_refs:
        return "stale"
    return "unknown"


def _derive_freshness_reason(market: dict, alert: dict, anomaly: dict) -> str:
    for candidate in (
        market.get("freshness_reason"),
        alert.get("freshness_reason"),
        anomaly.get("freshness_reason"),
    ):
        if candidate:
            return str(candidate)
    source_refs = market.get("upstream_refs", {}).get("source_refs") or []
    if "market_realtime" in source_refs:
        return "realtime market scan"
    if "latest_dashboard_rows" in source_refs:
        return "latest dashboard row"
    if "opportunity_board" in source_refs:
        return "opportunity board candidate"
    if "watchlist" in source_refs:
        return "watchlist candidate"
    if "seed" in source_refs:
        return "manual seed prior"
    return "unknown freshness source"


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}
