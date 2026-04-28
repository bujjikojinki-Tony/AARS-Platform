from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from weather_comparison_engine.ingest.realtime_forecast_loader import RealtimeForecastLoader
from weather_comparison_engine.monitoring_layer.family_scanner.family_scan_report_writer import (
    build_family_scan_report,
    write_family_scan_report,
    write_market_anomaly_events,
)
from weather_comparison_engine.monitoring_layer.market_scanner import (
    build_evidence_scan_snapshot,
    build_market_universe_snapshot,
    build_scan_status,
    write_evidence_scan_snapshot,
    write_market_universe_snapshot,
    write_scanner_status,
)
from weather_comparison_engine.monitoring_layer.alerting import (
    route_family_anomaly_events,
    route_market_alert_events,
    route_scanner_ops_alerts,
)
from weather_comparison_engine.monitoring_layer.observation_alert_layer.market_alert_event_writer import (
    build_market_alert_event,
    write_market_alert_event,
)
from weather_comparison_engine.settings import (
    COMPARISON_HISTORY_JSON,
    ALERTS_OUTPUT_DIR,
    EVIDENCE_SCAN_SNAPSHOT_JSON,
    FAMILY_ANOMALY_SUMMARY_JSON,
    MARKET_ALERT_EVENTS_JSON,
    MARKET_UNIVERSE_SNAPSHOT_JSON,
    SCAN_QUEUE_STATUS_JSON,
    SCANNER_OPS_ALERTS_JSON,
    SCANNER_STATUS_JSON,
    LATEST_DASHBOARD_ROWS_JSON,
    PROBABILITY_STATES_DIR,
    REALTIME_FORECAST_JSON,
    REALTIME_FORECAST_SNAPSHOTS_GLOB,
    RESOLVER_REPORT_JSON,
    SOURCE_POLICY_STATUS_JSON,
)

ROOT = Path(__file__).resolve().parents[3]

DEFAULT_OBSERVATION_SNAPSHOT_JSON = Path(
    os.getenv(
        "OBSERVATION_SNAPSHOT_JSON",
        str(ROOT.parent / "weather-dashboard" / "data" / "outputs" / "wunderground_shanghai_snapshot.json"),
    )
)
DEFAULT_MARKET_ALERT_EVENTS_DIR = Path(
    os.getenv(
        "MARKET_ALERT_EVENTS_DIR",
        str(ROOT / "data" / "outputs" / "market_alert_events"),
    )
)
DEFAULT_FAMILY_SCAN_REPORTS_DIR = Path(
    os.getenv(
        "FAMILY_SCAN_REPORTS_DIR",
        str(ROOT / "data" / "outputs" / "family_scan_reports"),
    )
)
DEFAULT_MARKET_ANOMALY_EVENTS_DIR = Path(
    os.getenv(
        "MARKET_ANOMALY_EVENTS_DIR",
        str(ROOT / "data" / "outputs" / "market_anomaly_events"),
    )
)
DEFAULT_SCANNER_OUTPUT_DIR = Path(
    os.getenv(
        "SCANNER_OUTPUT_DIR",
        str(ROOT / "data" / "outputs" / "scanner"),
    )
)
DEFAULT_ALERTS_OUTPUT_DIR = Path(
    os.getenv(
        "ALERTS_OUTPUT_DIR",
        str(ROOT / "data" / "outputs" / "alerts"),
    )
)


def load_latest_market_row() -> dict:
    if not LATEST_DASHBOARD_ROWS_JSON.exists():
        raise FileNotFoundError(f"Missing latest dashboard rows: {LATEST_DASHBOARD_ROWS_JSON}")
    rows = json.loads(LATEST_DASHBOARD_ROWS_JSON.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError("latest dashboard rows is empty")
    return rows[-1]


def load_matching_forecast_snapshot(market_id: str, forecast_loader: RealtimeForecastLoader | None = None) -> dict:
    loader = forecast_loader or RealtimeForecastLoader()
    try:
        snapshots = loader.load_many(REALTIME_FORECAST_SNAPSHOTS_GLOB)
    except Exception:
        snapshots = []

    for snapshot in snapshots:
        if str(snapshot.get("market_id") or "") == str(market_id):
            return snapshot

    if REALTIME_FORECAST_JSON.exists():
        return loader.load(REALTIME_FORECAST_JSON)
    raise FileNotFoundError(f"Missing realtime forecast snapshot: {REALTIME_FORECAST_JSON}")


def load_resolver_rule(market_id: str) -> dict:
    if not RESOLVER_REPORT_JSON.exists():
        return {}
    report = json.loads(RESOLVER_REPORT_JSON.read_text(encoding="utf-8"))
    rules = report.get("rules") or []
    for rule in rules:
        if str(rule.get("market_id") or "") == str(market_id):
            return rule
    return {}


def load_observation_snapshot() -> dict:
    if DEFAULT_OBSERVATION_SNAPSHOT_JSON.exists():
        return json.loads(DEFAULT_OBSERVATION_SNAPSHOT_JSON.read_text(encoding="utf-8"))
    return {}


def run_observation_alert_once(
    *,
    observation_snapshot: dict | None = None,
    market_row: dict | None = None,
    forecast_snapshot: dict | None = None,
    resolver_rule: dict | None = None,
    previous_observation_snapshot: dict | None = None,
    threshold_policy: dict | None = None,
    source_policy_status: dict | None = None,
    market_alert_events_dir: Path | None = None,
    now: datetime | None = None,
) -> dict:
    market_row = market_row or load_latest_market_row()
    market_id = str(market_row.get("market_id") or "")
    forecast_snapshot = forecast_snapshot or load_matching_forecast_snapshot(market_id)
    resolver_rule = resolver_rule or load_resolver_rule(market_id)
    observation_snapshot = observation_snapshot or load_observation_snapshot()
    source_policy_status = source_policy_status or _load_source_policy_status()

    if not resolver_rule:
        resolver_rule = {
            "market_id": market_id,
            "market_family": market_row.get("market_family") or forecast_snapshot.get("market_family"),
            "location_name": market_row.get("location_name") or forecast_snapshot.get("location_name"),
            "target_date": market_row.get("target_date") or forecast_snapshot.get("target_date"),
            "variable_name": market_row.get("variable_name") or forecast_snapshot.get("variable_name"),
            "source_match_grade": market_row.get("source_match_grade") or "unknown",
            "official_vs_proxy_source": market_row.get("official_vs_proxy_source") or "unknown",
            "freshness_status": market_row.get("freshness_status") or "unknown",
        }

    if not observation_snapshot:
        observation_snapshot = dict(market_row)
        observation_snapshot.setdefault("observation_value", market_row.get("market_probability"))
        observation_snapshot.setdefault("observed_at", market_row.get("updated_at"))

    event = build_market_alert_event(
        market_id=market_id,
        observation_snapshot=observation_snapshot,
        forecast_snapshot=forecast_snapshot,
        market_rule=resolver_rule,
        comparison_point=market_row,
        previous_observation_snapshot=previous_observation_snapshot or observation_snapshot,
        threshold_policy=threshold_policy or {"version": "v1", "threshold_value": {"threshold_cross_value": 30.0}},
        source_policy_status=source_policy_status,
        now=now,
    )
    out_dir = market_alert_events_dir or DEFAULT_MARKET_ALERT_EVENTS_DIR
    output_path = out_dir / f"market_alert_{market_id}_{event['generated_at'].replace(':', '').replace('-', '')}.json"
    write_market_alert_event(output_path, event)
    return {"output_path": str(output_path), "event": event}


def run_family_anomaly_scan_once(
    *,
    market_rows: list[dict] | None = None,
    comparison_history: list[dict] | None = None,
    probability_states: dict[str, dict] | None = None,
    source_policy_status: dict | None = None,
    family_scan_reports_dir: Path | None = None,
    market_anomaly_events_dir: Path | None = None,
    now: datetime | None = None,
) -> dict:
    market_rows = market_rows if market_rows is not None else _load_json(LATEST_DASHBOARD_ROWS_JSON, [])
    if not isinstance(market_rows, list):
        market_rows = []
    comparison_history = comparison_history if comparison_history is not None else _load_json(COMPARISON_HISTORY_JSON, [])
    if not isinstance(comparison_history, list):
        comparison_history = []
    probability_states = probability_states if probability_states is not None else _load_probability_states()
    source_policy_status = source_policy_status if source_policy_status is not None else _load_source_policy_status()

    report = build_family_scan_report(
        market_rows=market_rows,
        comparison_history=comparison_history,
        probability_states=probability_states,
        source_policy_status=source_policy_status,
        now=now,
    )
    out_dir = family_scan_reports_dir or DEFAULT_FAMILY_SCAN_REPORTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"family_scan_{report['generated_at'].replace(':', '').replace('-', '')}.json"
    write_family_scan_report(report_path, report)

    anomaly_events = report.get("anomaly_events") or []
    anomaly_dir = market_anomaly_events_dir or DEFAULT_MARKET_ANOMALY_EVENTS_DIR
    anomaly_dir.mkdir(parents=True, exist_ok=True)
    anomaly_events_path = anomaly_dir / f"market_anomaly_{report['generated_at'].replace(':', '').replace('-', '')}.jsonl"
    write_market_anomaly_events(anomaly_events_path, anomaly_events)

    return {
        "report_path": str(report_path),
        "anomaly_events_path": str(anomaly_events_path),
        "family_count": report.get("family_count"),
        "market_count": report.get("market_count"),
        "top_anomalies": report.get("top_anomalies", [])[:3],
        "report": report,
    }


def run_market_discovery_scan_once(
    *,
    opportunity_seed_path: Path | None = None,
    opportunity_board_path: Path | None = None,
    latest_dashboard_rows_path: Path | None = None,
    market_realtime_path: Path | None = None,
    watchlist_path: Path | None = None,
    output_path: Path | None = None,
    now: datetime | None = None,
) -> dict:
    snapshot = build_market_universe_snapshot(
        opportunity_seed_path=opportunity_seed_path,
        opportunity_board_path=opportunity_board_path,
        latest_dashboard_rows_path=latest_dashboard_rows_path,
        market_realtime_path=market_realtime_path,
        watchlist_path=watchlist_path,
        now=now,
    )
    path = write_market_universe_snapshot(output_path or DEFAULT_SCANNER_OUTPUT_DIR / "market_universe_snapshot.json", snapshot)
    return {"output_path": str(path), "snapshot": snapshot}


def run_evidence_scan_once(
    *,
    market_universe_snapshot: dict | None = None,
    output_path: Path | None = None,
    now: datetime | None = None,
) -> dict:
    snapshot = build_evidence_scan_snapshot(
        market_universe_snapshot=market_universe_snapshot,
        now=now,
    )
    path = write_evidence_scan_snapshot(output_path or EVIDENCE_SCAN_SNAPSHOT_JSON, snapshot)
    return {"output_path": str(path), "snapshot": snapshot}


def run_scanner_status_once(
    *,
    market_universe_snapshot: dict | None = None,
    evidence_scan_snapshot: dict | None = None,
    alert_events: list[dict] | None = None,
    output_path: Path | None = None,
    now: datetime | None = None,
) -> dict:
    status = build_scan_status(
        market_universe_snapshot=market_universe_snapshot,
        evidence_scan_snapshot=evidence_scan_snapshot,
        alert_events=alert_events,
        now=now,
    )
    path = write_scanner_status(output_path or SCANNER_STATUS_JSON, status)
    return {"output_path": str(path), "status": status}


def run_alert_router_once(
    *,
    market_alert_events: list[dict] | None = None,
    family_anomaly_report: dict | None = None,
    scanner_ops_alerts: list[dict] | None = None,
    now: datetime | None = None,
) -> dict:
    market_alert_events = market_alert_events if market_alert_events is not None else _load_json_records(DEFAULT_MARKET_ALERT_EVENTS_DIR)
    family_anomaly_report = family_anomaly_report if family_anomaly_report is not None else _load_latest_json_dict(DEFAULT_FAMILY_SCAN_REPORTS_DIR)
    scanner_ops_alerts = scanner_ops_alerts if scanner_ops_alerts is not None else []

    market_routed = route_market_alert_events(
        events=market_alert_events,
        output_path=MARKET_ALERT_EVENTS_JSON,
        queue_status_path=SCAN_QUEUE_STATUS_JSON,
        now=now,
    )
    family_routed = route_family_anomaly_events(
        report=family_anomaly_report if isinstance(family_anomaly_report, dict) else {},
        output_path=FAMILY_ANOMALY_SUMMARY_JSON,
        now=now,
    )
    ops_routed = route_scanner_ops_alerts(
        alerts=scanner_ops_alerts,
        output_path=SCANNER_OPS_ALERTS_JSON,
        now=now,
    )
    return {
        "market": market_routed,
        "family": family_routed,
        "ops": ops_routed,
    }


def _load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _load_probability_states() -> dict[str, dict]:
    states: dict[str, dict] = {}
    if PROBABILITY_STATES_DIR.exists():
        for path in PROBABILITY_STATES_DIR.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            market_id = str(payload.get("market_id") or "")
            if market_id:
                states[market_id] = payload
    return states


def _load_source_policy_status() -> dict:
    if SOURCE_POLICY_STATUS_JSON.exists():
        payload = _load_json(SOURCE_POLICY_STATUS_JSON, {})
        return payload if isinstance(payload, dict) else {}
    return {}


def _load_json_records(directory: Path) -> list[dict]:
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
    return records


def _load_latest_json_dict(directory: Path) -> dict:
    if not directory.exists():
        return {}
    candidates = sorted(directory.glob("*.json"), key=lambda path: path.stat().st_mtime if path.exists() else 0, reverse=True)
    if not candidates:
        return {}
    try:
        payload = json.loads(candidates[0].read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}
