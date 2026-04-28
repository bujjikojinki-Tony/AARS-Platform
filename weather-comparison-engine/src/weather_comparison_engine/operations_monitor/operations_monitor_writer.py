from __future__ import annotations

import json
from pathlib import Path

from weather_comparison_engine.operations_monitor.operations_monitor_view_builder import (
    build_operations_monitor_view_from_files,
)


def write_operations_monitor_view(path: str | Path, payload: dict) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def write_operations_monitor_artifacts(
    *,
    view_path: str | Path,
    summary_path: str | Path,
    payload: dict,
) -> dict[str, Path]:
    view_out = write_operations_monitor_view(view_path, payload)
    summary_out = Path(summary_path)
    summary_out.parent.mkdir(parents=True, exist_ok=True)
    summary_out.write_text(
        json.dumps(_build_summary_artifact(payload), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return {"view": view_out, "summary": summary_out}


def write_operations_monitor_from_files(
    *,
    view_path: str | Path,
    summary_path: str | Path,
    **kwargs,
) -> dict[str, Path]:
    payload = build_operations_monitor_view_from_files(**kwargs)
    return write_operations_monitor_artifacts(view_path=view_path, summary_path=summary_path, payload=payload)


def _build_summary_artifact(payload: dict) -> dict:
    global_summary = payload.get("global_summary") or {}
    selected_detail = payload.get("selected_market_quick_detail") or {}
    system_health = payload.get("system_health") or {}
    scanner_health = system_health.get("scanner_health") or {}
    source_health = system_health.get("source_health") or {}
    queue_health = system_health.get("queue_health") or {}
    return {
        "schema_version": "operations_monitor_summary.v1",
        "generated_at": payload.get("generated_at"),
        "selected_market_id": (payload.get("view_context") or {}).get("selected_market_id") or "-",
        "markets_scanned": global_summary.get("markets_scanned"),
        "focus_markets_count": global_summary.get("focus_markets_count"),
        "fresh_ratio": global_summary.get("fresh_ratio"),
        "high_alert_markets": global_summary.get("high_alert_markets"),
        "high_anomaly_markets": global_summary.get("high_anomaly_markets"),
        "gate_blocked_markets": global_summary.get("gate_blocked_markets"),
        "ops_alert_count": global_summary.get("ops_alert_count"),
        "scanner_status": scanner_health.get("status"),
        "scanner_next_scan_eta": scanner_health.get("next_scan_eta"),
        "source_status": source_health.get("overall_status"),
        "queue_accepted_count": queue_health.get("accepted_count"),
        "queue_suppressed_count": queue_health.get("suppressed_count"),
        "recommended_operator_action": selected_detail.get("recommended_operator_action") or "-",
        "primary_warning": _first_non_empty(
            _first_problem_reason(source_health.get("problem_sources") or []),
            _first_ops_alert_reason(payload.get("ops_alerts") or []),
            "all clear",
        ),
        "focus_markets": [
            {
                "market_id": item.get("market_id"),
                "market_family": item.get("market_family"),
                "focus_reason": item.get("focus_reason"),
            }
            for item in (payload.get("focus_markets") or [])[:5]
            if isinstance(item, dict)
        ],
        "selected_market_summary": {
            "market_question": selected_detail.get("market_question"),
            "execution_boundary": selected_detail.get("execution_boundary"),
            "market_family": selected_detail.get("market_family"),
        },
    }


def _first_problem_reason(problem_sources: list[dict]) -> str:
    for source in problem_sources:
        reason = source.get("status_reason") if isinstance(source, dict) else None
        if isinstance(reason, str) and reason.strip():
            return reason.strip()
    return "-"


def _first_ops_alert_reason(ops_alerts: list[dict]) -> str:
    for alert in ops_alerts:
        reason = alert.get("primary_reason") if isinstance(alert, dict) else None
        if isinstance(reason, str) and reason.strip():
            return reason.strip()
    return "-"


def _first_non_empty(*values: object) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "-"
