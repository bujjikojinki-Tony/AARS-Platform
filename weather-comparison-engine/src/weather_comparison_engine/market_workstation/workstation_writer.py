from __future__ import annotations

import json
from pathlib import Path

from weather_comparison_engine.market_workstation.market_workstation_view_builder import (
    build_market_workstation_view,
)
from weather_comparison_engine.status.top_parameter_view import build_top_parameter_view


def build_market_workstation_from_files(
    *,
    market_id: str,
    page_context: dict | None = None,
    latest_dashboard_rows_path: Path,
    comparison_history_path: Path,
    forecast_snapshot_path: Path | None = None,
    forecast_snapshots_glob: str | None = None,
    gate_stack_api_path: Path | None = None,
    opportunity_board_path: Path | None = None,
    model_validation_report_path: Path | None = None,
    validation_freshness_status_path: Path | None = None,
    label_coverage_report_path: Path | None = None,
    market_alert_events_dir: Path | None = None,
    market_anomaly_events_dir: Path | None = None,
    family_scan_reports_dir: Path | None = None,
    ops_alerts_jsonl_path: Path | None = None,
) -> dict:
    rows = _load_json(latest_dashboard_rows_path)
    rows = rows if isinstance(rows, list) else []
    market_row = _find_row(rows, market_id)
    if not market_row:
        raise FileNotFoundError(f"No latest dashboard row found for market_id={market_id}")

    history_rows = _filter_history(_load_json(comparison_history_path), market_id)
    forecast_snapshot = _load_forecast_snapshot(
        market_id=market_id,
        forecast_snapshot_path=forecast_snapshot_path,
        forecast_snapshots_glob=forecast_snapshots_glob,
    )
    gate_summary = _build_gate_summary(_load_json(gate_stack_api_path) if gate_stack_api_path else {}, market_id)
    opportunity_context = _find_opportunity_context(_load_json(opportunity_board_path) if opportunity_board_path else {}, market_id, market_row)
    validation_summary = _build_validation_summary(
        model_validation=_load_json(model_validation_report_path) if model_validation_report_path else {},
        freshness=_load_json(validation_freshness_status_path) if validation_freshness_status_path else {},
        coverage=_load_json(label_coverage_report_path) if label_coverage_report_path else {},
    )
    latest_alert = _load_latest_market_alert(market_alert_events_dir, market_id)
    latest_anomaly = _load_latest_market_anomaly(market_anomaly_events_dir, market_id)
    latest_family_scan_report = _load_latest_family_scan_report(family_scan_reports_dir)
    latest_ops = _load_latest_jsonl(ops_alerts_jsonl_path)
    top_parameter_view = build_top_parameter_view(
        current_market=market_row,
        forecast_snapshot=forecast_snapshot,
        comparison_point=market_row,
    )
    return build_market_workstation_view(
        selected_market_id=market_id,
        top_parameter_view=top_parameter_view,
        page_context=page_context,
        resolver_rule=market_row,
        comparison_row=market_row,
        gate_summary=gate_summary,
        opportunity_context=opportunity_context,
        validation_summary=validation_summary,
        forecast_snapshot=forecast_snapshot,
        observation_snapshot={},
        evidence_history_rows=history_rows,
        latest_alert=latest_alert,
        latest_anomaly=latest_anomaly,
        latest_ops=latest_ops,
        latest_family_scan_report=latest_family_scan_report,
    )


def write_market_workstation_artifacts(*, output_dir: Path, market_id: str, view: dict) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_market_id = _slugify(market_id)
    paths = {
        "workstation": output_dir / f"market_workstation_{safe_market_id}.json",
        "rule_source_model_panel": output_dir / f"rule_source_model_panel_{safe_market_id}.json",
        "evidence_timeline": output_dir / f"evidence_timeline_{safe_market_id}.json",
        "validation_compare": output_dir / f"validation_compare_{safe_market_id}.json",
        "gate_advisory_panel": output_dir / f"gate_advisory_panel_{safe_market_id}.json",
        "summary": output_dir / f"market_workstation_summary_{safe_market_id}.json",
    }
    paths["workstation"].write_text(json.dumps(view, indent=2, ensure_ascii=False), encoding="utf-8")
    paths["rule_source_model_panel"].write_text(
        json.dumps(view.get("rule_source_model_panel") or {}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    paths["evidence_timeline"].write_text(
        json.dumps(view.get("evidence_timeline") or {}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    paths["validation_compare"].write_text(
        json.dumps(view.get("validation_compare_panel") or {}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    paths["gate_advisory_panel"].write_text(
        json.dumps(view.get("gate_advisory_panel") or {}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    paths["summary"].write_text(
        json.dumps(_build_workstation_summary(view), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return paths


def _find_row(rows: list[dict], market_id: str) -> dict:
    for row in rows:
        if isinstance(row, dict) and str(row.get("market_id") or "") == str(market_id):
            return row
    return {}


def _build_workstation_summary(view: dict) -> dict:
    top = view.get("top_parameter_view") if isinstance(view.get("top_parameter_view"), dict) else {}
    gate_panel = view.get("gate_advisory_panel") if isinstance(view.get("gate_advisory_panel"), dict) else {}
    gate = gate_panel.get("gate_summary") if isinstance(gate_panel.get("gate_summary"), dict) else {}
    advisory = gate_panel.get("advisory_summary") if isinstance(gate_panel.get("advisory_summary"), dict) else {}
    latest_alert = view.get("latest_alert") if isinstance(view.get("latest_alert"), dict) else {}
    latest_anomaly = view.get("latest_anomaly") if isinstance(view.get("latest_anomaly"), dict) else {}
    return {
        "schema_version": "market_workstation_summary.v1",
        "generated_at": view.get("generated_at"),
        "market_id": view.get("selected_market_id"),
        "market_question": top.get("market_question"),
        "latest_alert_severity": latest_alert.get("severity") or "-",
        "latest_anomaly_score": latest_anomaly.get("anomaly_score"),
        "can_execute": gate.get("can_execute"),
        "primary_block_reason": gate.get("primary_block_reason"),
        "recommended_operator_action": advisory.get("recommended_operator_action"),
        "execution_boundary": (gate_panel.get("dry_run_area") or {}).get("execution_boundary"),
    }


def _filter_history(payload: object, market_id: str) -> list[dict]:
    if not isinstance(payload, list):
        return []
    rows = [row for row in payload if isinstance(row, dict) and str(row.get("market_id") or "") == str(market_id)]
    rows.sort(key=lambda row: str(row.get("timestamp") or ""))
    return rows[-20:]


def _load_forecast_snapshot(
    *,
    market_id: str,
    forecast_snapshot_path: Path | None,
    forecast_snapshots_glob: str | None,
) -> dict:
    if forecast_snapshots_glob:
        for path in sorted(Path().glob(forecast_snapshots_glob)):
            payload = _load_json(path)
            if isinstance(payload, dict) and str(payload.get("market_id") or "") == str(market_id):
                return payload
    payload = _load_json(forecast_snapshot_path) if forecast_snapshot_path else {}
    return payload if isinstance(payload, dict) else {}


def _build_gate_summary(payload: object, market_id: str) -> dict:
    payload = payload if isinstance(payload, dict) else {}
    candidates = payload.get("market_gate_views") or []
    gate = {}
    for item in candidates:
        if isinstance(item, dict) and str(item.get("market_id") or "") == str(market_id):
            gate = item
            break
    if not gate:
        gate = payload
    return {
        "gate_status": gate.get("gate_status") or gate.get("execution_gate") or payload.get("gate_status"),
        "data_gate": gate.get("data_gate") or "-",
        "resolver_gate": gate.get("resolver_gate") or "-",
        "probability_gate": gate.get("probability_gate") or "-",
        "freshness_gate": gate.get("freshness_gate") or "-",
        "authorization_gate": gate.get("authorization_gate") or "-",
        "execution_gate": gate.get("execution_gate") or "-",
        "blockers": gate.get("block_reasons") or gate.get("resolver_gate_reasons") or payload.get("block_reasons") or [],
        "recommended_operator_action": gate.get("recommended_operator_action") or payload.get("recommended_operator_action"),
        "gate_source": gate.get("gate_source") or payload.get("gate_source") or "gate_stack_api.v1",
    }


def _find_opportunity_context(payload: object, market_id: str, market_row: dict) -> dict:
    rows = payload.get("rows") if isinstance(payload, dict) else []
    rows = rows if isinstance(rows, list) else []
    for row in rows:
        if not isinstance(row, dict):
            continue
        market_ids = (row.get("upstream_refs") or {}).get("market_ids") or []
        if str(market_id) in {str(item) for item in market_ids}:
            return row
    city = str(market_row.get("city") or market_row.get("location_name") or "").strip().lower()
    family = str(market_row.get("market_family") or "").strip().lower()
    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("city") or "").strip().lower() == city and str(row.get("market_family") or "").strip().lower() == family:
            return row
    return {}


def _build_validation_summary(*, model_validation: object, freshness: object, coverage: object) -> dict:
    model_validation = model_validation if isinstance(model_validation, dict) else {}
    freshness = freshness if isinstance(freshness, dict) else {}
    coverage = coverage if isinstance(coverage, dict) else {}
    metrics = model_validation.get("validation_metrics") if isinstance(model_validation.get("validation_metrics"), dict) else {}
    promotion = model_validation.get("promotion_state") if isinstance(model_validation.get("promotion_state"), dict) else {}
    blockers: list[str] = []
    if str(freshness.get("status") or "").lower() not in {"healthy", "ok", "fresh"}:
        blockers.append(f"freshness:{freshness.get('status') or 'unknown'}")
    if str(coverage.get("status") or "").lower() not in {"healthy", "ok"}:
        blockers.append(f"coverage:{coverage.get('status') or 'unknown'}")
    return {
        "promotion_state": promotion.get("probability_mode") or model_validation.get("probability_mode") or "-",
        "promotion_reason": promotion.get("promotion_reason") or model_validation.get("promotion_reason") or "-",
        "demotion_reason": promotion.get("demotion_reason") or model_validation.get("demotion_reason") or "-",
        "freshness_status": freshness.get("status") or "-",
        "freshness_seconds": freshness.get("freshness_seconds") or "-",
        "coverage_status": coverage.get("status") or "-",
        "labeled_ratio": coverage.get("labeled_ratio") or "-",
        "sample_count": model_validation.get("sample_count") or "-",
        "labeled_sample_count": model_validation.get("labeled_sample_count") or "-",
        "calibration_status": model_validation.get("calibration_status") or "-",
        "brier_score": metrics.get("brier_score") or "-",
        "calibration_error": metrics.get("calibration_error") or "-",
        "blockers": blockers,
    }


def _load_latest_market_alert(directory: Path | None, market_id: str) -> dict:
    if directory is None or not directory.exists():
        return {}
    for path in sorted(directory.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        payload = _load_json(path)
        if isinstance(payload, dict) and str(payload.get("market_id") or "") == str(market_id):
            return payload
    return {}


def _load_latest_market_anomaly(directory: Path | None, market_id: str) -> dict:
    if directory is None or not directory.exists():
        return {}
    for path in sorted(directory.glob("*.jsonl"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        except Exception:
            continue
        for line in reversed(lines):
            try:
                payload = json.loads(line)
            except Exception:
                continue
            if isinstance(payload, dict) and str(payload.get("market_id") or "") == str(market_id):
                return payload
    return {}


def _load_latest_family_scan_report(directory: Path | None) -> dict:
    if not directory or not directory.exists():
        return {}
    candidates = sorted(directory.glob("*.json"), key=_sort_key, reverse=True)
    if not candidates:
        return {}
    try:
        payload = json.loads(candidates[0].read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_latest_jsonl(path: Path | None) -> dict:
    if path is None or not path.exists():
        return {}
    try:
        lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except Exception:
        return {}
    if not lines:
        return {}
    try:
        payload = json.loads(lines[-1])
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_json(path: Path | None) -> object:
    if path is None or not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _slugify(value: str) -> str:
    slug = str(value or "unknown").strip().replace("/", "_").replace(" ", "_")
    return "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in slug) or "unknown"
