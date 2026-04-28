from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from weather_telegram_console.settings import (
    get_scan_queue_status_path,
    get_scanner_status_path,
    get_market_universe_snapshot_path,
    get_evidence_scan_snapshot_path,
    get_family_scan_reports_dir,
    get_market_alert_events_dir,
    get_market_anomaly_events_dir,
    get_gate_stack_api_path,
    get_unified_status_path,
    get_source_policy_status_path,
)


class MonitoringAPI:
    def load_latest_monitoring_signals(self) -> dict:
        latest_alert = _load_latest_json(get_market_alert_events_dir(), suffix=".json")
        latest_report = _load_latest_json(get_family_scan_reports_dir(), suffix=".json")
        latest_anomaly = _load_latest_jsonl(get_market_anomaly_events_dir())
        latest_scanner_status = _load_json_file(get_scanner_status_path())
        latest_market_universe = _load_json_file(get_market_universe_snapshot_path())
        latest_evidence_scan = _load_json_file(get_evidence_scan_snapshot_path())
        latest_queue_status = _load_json_file(get_scan_queue_status_path())
        latest_gate_stack_api = _load_json_file(get_gate_stack_api_path())
        latest_unified_status = _load_json_file(get_unified_status_path())
        source_policy = _load_json_file(get_source_policy_status_path())
        runtime_block = _build_runtime_block_summary(latest_gate_stack_api, latest_unified_status)
        trend = self.load_monitoring_trend()
        operator_summary = _build_operator_summary(latest_alert, latest_report, latest_anomaly, runtime_block)
        return {
            "schema_version": "monitoring_signals.v1",
            "latest_alert": latest_alert,
            "latest_family_scan_report": latest_report,
            "latest_anomaly_event": latest_anomaly,
            "latest_scanner_status": latest_scanner_status,
            "latest_market_universe_snapshot": latest_market_universe,
            "latest_evidence_scan_snapshot": latest_evidence_scan,
            "latest_scan_queue_status": latest_queue_status,
            "latest_gate_stack_api": latest_gate_stack_api,
            "latest_unified_status": latest_unified_status,
            "latest_source_policy_status": source_policy,
            "runtime_block": runtime_block,
            "operator_summary": operator_summary,
            "trend": trend,
            "alert_count": _count_files(get_market_alert_events_dir(), suffix=".json"),
            "family_scan_count": _count_files(get_family_scan_reports_dir(), suffix=".json"),
            "anomaly_event_count": _count_files(get_market_anomaly_events_dir(), suffix=".jsonl"),
        }

    def load_monitoring_trend(self, limit: int = 5) -> dict:
        alerts = _load_recent_json(get_market_alert_events_dir(), suffix=".json", limit=limit)
        reports = _load_recent_json(get_family_scan_reports_dir(), suffix=".json", limit=limit)
        anomalies = _load_recent_jsonl(get_market_anomaly_events_dir(), limit=limit)
        severity_counts: dict[str, int] = {}
        for item in alerts:
            severity = str(item.get("severity") or "unknown").lower()
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        return {
            "window": limit,
            "severity_counts": severity_counts,
            "recent_alerts": alerts,
            "recent_family_reports": reports,
            "recent_anomalies": anomalies,
        }


def _load_latest_json(directory: Path, *, suffix: str) -> dict:
    if not directory.exists():
        return {}
    candidates = sorted(directory.glob(f"*{suffix}"), key=_sort_key, reverse=True)
    if not candidates:
        return {}
    try:
        return json.loads(candidates[0].read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_latest_jsonl(directory: Path) -> dict:
    if not directory.exists():
        return {}
    candidates = sorted(directory.glob("*.jsonl"), key=_sort_key, reverse=True)
    if not candidates:
        return {}
    try:
        lines = [line.strip() for line in candidates[0].read_text(encoding="utf-8").splitlines() if line.strip()]
    except Exception:
        return {}
    if not lines:
        return {}
    try:
        return json.loads(lines[-1])
    except Exception:
        return {}

def _load_recent_json(directory: Path, *, suffix: str, limit: int) -> list[dict]:
    if not directory.exists():
        return []
    candidates = sorted(directory.glob(f"*{suffix}"), key=_sort_key, reverse=True)[:limit]
    records: list[dict] = []
    for path in candidates:
        try:
            records.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return records


def _load_recent_jsonl(directory: Path, *, limit: int) -> list[dict]:
    if not directory.exists():
        return []
    candidates = sorted(directory.glob("*.jsonl"), key=_sort_key, reverse=True)[:limit]
    records: list[dict] = []
    for path in candidates:
        try:
            lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        except Exception:
            continue
        if not lines:
            continue
        try:
            records.append(json.loads(lines[-1]))
        except Exception:
            continue
    return records


def _load_json_file(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _count_files(directory: Path, *, suffix: str) -> int:
    if not directory.exists():
        return 0
    return sum(1 for path in directory.glob(f"*{suffix}") if path.is_file())


def _sort_key(path: Path) -> datetime:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)


def _build_runtime_block_summary(
    gate_stack_api: dict | None,
    unified_status: dict | None,
) -> dict:
    gate_stack_api = gate_stack_api if isinstance(gate_stack_api, dict) else {}
    unified_status = unified_status if isinstance(unified_status, dict) else {}
    gate_stack = unified_status.get("gate_stack") if isinstance(unified_status.get("gate_stack"), dict) else {}
    execution = unified_status.get("execution") if isinstance(unified_status.get("execution"), dict) else {}
    block_reasons = [
        str(item)
        for item in (
            gate_stack_api.get("block_reasons")
            or unified_status.get("block_reasons")
            or gate_stack.get("block_reasons")
            or []
        )
        if item
    ]
    return {
        "schema_version": "monitoring_runtime_block.v1",
        "overall_status": str(gate_stack_api.get("overall_status") or unified_status.get("overall_status") or "-"),
        "gate_status": str(gate_stack_api.get("gate_status") or gate_stack.get("execution_gate") or "-"),
        "execution_status": str(execution.get("status") or unified_status.get("execution_status") or "-"),
        "ready_for_live": bool(gate_stack_api.get("can_execute", unified_status.get("ready_for_live", False))),
        "can_execute": bool(gate_stack_api.get("can_execute", execution.get("ready_for_live", False))),
        "primary_block_reason": str(
            gate_stack_api.get("primary_block_reason")
            or execution.get("primary_block_reason")
            or gate_stack.get("primary_block_reason")
            or (block_reasons[0] if block_reasons else "-")
        ),
        "recommended_operator_action": str(
            gate_stack_api.get("recommended_operator_action")
            or unified_status.get("recommended_operator_action")
            or execution.get("recommended_operator_action")
            or "hold_execution_and_review"
        ),
        "gate_source": str(
            gate_stack_api.get("gate_source")
            or unified_status.get("gate_source")
            or gate_stack.get("gate_source")
            or "local_fallback"
        ),
        "block_reasons": block_reasons,
        "block_reason_count": len(block_reasons),
    }


def _build_operator_summary(
    latest_alert: dict | None,
    latest_report: dict | None,
    latest_anomaly: dict | None,
    runtime_block: dict | None,
) -> dict:
    latest_alert = latest_alert if isinstance(latest_alert, dict) else {}
    latest_report = latest_report if isinstance(latest_report, dict) else {}
    latest_anomaly = latest_anomaly if isinstance(latest_anomaly, dict) else {}
    runtime_block = runtime_block if isinstance(runtime_block, dict) else {}
    severity = str(latest_alert.get("severity") or "info").lower()
    anomaly_bucket = str(latest_anomaly.get("anomaly_bucket") or "-").lower()
    gate_status = str(runtime_block.get("gate_status") or "-").lower()
    if gate_status in {"blocked", "block", "blocked"}:
        action = "review_gate_block"
    elif severity in {"red", "critical"}:
        action = "review_market_alert"
    elif anomaly_bucket in {"high", "medium"}:
        action = "review_family_anomaly"
    else:
        action = "monitor_and_wait"
    reason = (
        latest_alert.get("primary_reason")
        or latest_anomaly.get("primary_reason")
        or runtime_block.get("primary_block_reason")
        or "-"
    )
    return {
        "schema_version": "operator_summary.v1",
        "current_focus": latest_alert.get("market_id") or latest_anomaly.get("market_id") or "-",
        "current_family": latest_alert.get("market_family") or latest_anomaly.get("market_family") or _top_family(latest_report),
        "alert_severity": severity,
        "anomaly_bucket": anomaly_bucket,
        "gate_status": gate_status,
        "recommended_operator_action": action,
        "primary_reason": str(reason),
        "summary_line": _build_summary_line(action=action, reason=reason, gate_status=gate_status, severity=severity, anomaly_bucket=anomaly_bucket),
        "next_step": _build_next_step(action=action, gate_status=gate_status, severity=severity, anomaly_bucket=anomaly_bucket),
        "is_blocked": gate_status == "blocked",
        "is_high_alert": severity in {"red", "critical"},
        "is_high_anomaly": anomaly_bucket == "high",
    }


def _top_family(report: dict | None) -> object:
    report = report if isinstance(report, dict) else {}
    summaries = report.get("family_summaries") or []
    if not summaries:
        return "-"
    ranked = sorted(
        (summary for summary in summaries if isinstance(summary, dict)),
        key=lambda item: float(item.get("max_intervention_like_score") or 0.0),
        reverse=True,
    )
    return ranked[0].get("market_family") if ranked else "-"


def _build_summary_line(
    *,
    action: str,
    reason: object,
    gate_status: str,
    severity: str,
    anomaly_bucket: str,
) -> str:
    reason_text = str(reason or "-")
    if gate_status == "blocked":
        return f"Gate blocked; review {reason_text}"
    if severity in {"red", "critical"}:
        return f"High alert; review {reason_text}"
    if anomaly_bucket in {"high", "medium"}:
        return f"Family anomaly elevated; review {reason_text}"
    return f"Stable; {reason_text}"


def _build_next_step(*, action: str, gate_status: str, severity: str, anomaly_bucket: str) -> str:
    if gate_status == "blocked":
        return "review_gate_block"
    if severity in {"red", "critical"}:
        return "review_market_alert"
    if anomaly_bucket in {"high", "medium"}:
        return "review_family_anomaly"
    return action
