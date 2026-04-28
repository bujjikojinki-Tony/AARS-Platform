from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_opportunity_feature_context(
    *,
    latest_dashboard_rows_path: Path,
    gate_stack_api_path: Path,
    unified_status_path: Path,
    model_validation_report_path: Path | None = None,
    source_policy_status_path: Path | None = None,
    opportunity_seed_list_path: Path | None = None,
    market_alert_events_dir: Path | None = None,
    market_anomaly_events_dir: Path | None = None,
    family_scan_reports_dir: Path | None = None,
    comparison_history_path: Path | None = None,
) -> dict:
    latest_dashboard_rows = _load_json(latest_dashboard_rows_path)
    gate_stack_api = _load_json(gate_stack_api_path)
    unified_status = _load_json(unified_status_path)
    model_validation_report = _load_json(model_validation_report_path) if model_validation_report_path else {}
    source_policy_status = _load_json(source_policy_status_path) if source_policy_status_path else {}
    opportunity_seed_list = _load_json(opportunity_seed_list_path) if opportunity_seed_list_path else {}
    comparison_history = _load_json_list(comparison_history_path) if comparison_history_path else []

    latest_alerts = _load_latest_json_records(market_alert_events_dir, suffix=".json") if market_alert_events_dir else []
    latest_anomalies = _load_latest_jsonl_records(market_anomaly_events_dir) if market_anomaly_events_dir else []
    latest_family_reports = _load_latest_json_records(family_scan_reports_dir, suffix=".json") if family_scan_reports_dir else []
    alert_index = _index_by_market_id(latest_alerts)
    anomaly_index = _index_by_market_id(latest_anomalies)
    gate_index = _index_gate_views(gate_stack_api)
    comparison_index = _index_comparison_history(comparison_history)

    return {
        "latest_dashboard_rows": latest_dashboard_rows if isinstance(latest_dashboard_rows, list) else [],
        "gate_stack_api": gate_stack_api if isinstance(gate_stack_api, dict) else {},
        "unified_status": unified_status if isinstance(unified_status, dict) else {},
        "model_validation_report": model_validation_report if isinstance(model_validation_report, dict) else {},
        "source_policy_status": source_policy_status if isinstance(source_policy_status, dict) else {},
        "opportunity_seed_list": opportunity_seed_list if isinstance(opportunity_seed_list, dict) else {},
        "comparison_history": comparison_history if isinstance(comparison_history, list) else [],
        "latest_alerts": latest_alerts,
        "latest_anomalies": latest_anomalies,
        "latest_family_reports": latest_family_reports,
        "alert_index": alert_index,
        "anomaly_index": anomaly_index,
        "gate_index": gate_index,
        "comparison_index": comparison_index,
    }


def _load_json(path: Path | None) -> Any:
    if not path:
        return {}
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload


def _load_json_list(path: Path | None) -> list[dict]:
    payload = _load_json(path)
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _load_latest_json_records(directory: Path | None, *, suffix: str) -> list[dict]:
    if not directory or not directory.exists():
        return []
    records: list[dict] = []
    for path in sorted(directory.glob(f"*{suffix}"), key=_sort_key, reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(payload, dict):
            records.append(payload)
    return records


def _load_latest_jsonl_records(directory: Path | None) -> list[dict]:
    if not directory or not directory.exists():
        return []
    records: list[dict] = []
    for path in sorted(directory.glob("*.jsonl"), key=_sort_key, reverse=True):
        try:
            lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        except Exception:
            continue
        if not lines:
            continue
        try:
            payload = json.loads(lines[-1])
        except Exception:
            continue
        if isinstance(payload, dict):
            records.append(payload)
    return records


def _index_by_market_id(records: list[dict]) -> dict[str, dict]:
    indexed: dict[str, dict] = {}
    for record in records:
        market_id = str(record.get("market_id") or "").strip()
        if not market_id:
            continue
        if market_id not in indexed:
            indexed[market_id] = record
    return indexed


def _index_gate_views(gate_stack_api: dict | None) -> dict[str, dict]:
    if not isinstance(gate_stack_api, dict):
        return {}
    views = gate_stack_api.get("market_gate_views") or []
    if not isinstance(views, list):
        return {}
    indexed: dict[str, dict] = {}
    for view in views:
        if not isinstance(view, dict):
            continue
        market_id = str(view.get("market_id") or "").strip()
        if not market_id:
            continue
        if market_id not in indexed:
            indexed[market_id] = view
    return indexed


def _index_comparison_history(records: list[dict]) -> dict[str, dict]:
    indexed: dict[str, dict] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        market_id = str(record.get("market_id") or "").strip()
        if not market_id:
            continue
        current = indexed.get(market_id)
        if current is None or str(record.get("timestamp") or "") > str(current.get("timestamp") or ""):
            indexed[market_id] = record
    return indexed


def _sort_key(path: Path) -> datetime:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)
