from __future__ import annotations

from weather_telegram_console.bot.formatters.telegram_text import md_line


def format_monitoring_card(payload: dict) -> str:
    latest_alert = payload.get("latest_alert") or {}
    latest_report = payload.get("latest_family_scan_report") or {}
    latest_anomaly = payload.get("latest_anomaly_event") or {}
    latest_scanner_status = payload.get("latest_scanner_status") or {}
    latest_market_universe = payload.get("latest_market_universe_snapshot") or {}
    latest_evidence_scan = payload.get("latest_evidence_scan_snapshot") or {}
    latest_queue_status = payload.get("latest_scan_queue_status") or {}
    latest_source_policy = payload.get("latest_source_policy_status") or {}
    runtime_block = payload.get("runtime_block") or {}
    operator_summary = payload.get("operator_summary") or {}
    trend = payload.get("trend") or {}
    severity_counts = trend.get("severity_counts") or {}
    recent_alerts = trend.get("recent_alerts") or []
    recent_anomalies = trend.get("recent_anomalies") or []
    scan_ratio = (
        f"{latest_scanner_status.get('fresh_markets', 0)} / "
        f"{latest_scanner_status.get('stale_markets', 0)} / "
        f"{latest_scanner_status.get('unavailable_markets', 0)}"
    )
    queue_ratio = (
        f"{latest_queue_status.get('accepted_count', 0)} / "
        f"{latest_queue_status.get('suppressed_count', 0)}"
    )
    return (
        "*AARS Monitoring Signals*\n"
        f"{md_line('Alert Count', payload.get('alert_count'))}\n"
        f"{md_line('Family Scan Count', payload.get('family_scan_count'))}\n"
        f"{md_line('Anomaly Event Count', payload.get('anomaly_event_count'))}\n\n"
        "*Latest Market Alert*\n"
        f"{md_line('Market', latest_alert.get('market_id'))}\n"
        f"{md_line('Family', latest_alert.get('market_family'))}\n"
        f"{md_line('Severity', latest_alert.get('severity'))}\n"
        f"{md_line('Reason', latest_alert.get('primary_reason'))}\n"
        f"{md_line('Governance', latest_alert.get('governance_reason'))}\n"
        f"{md_line('Action', latest_alert.get('recommended_operator_action'))}\n"
        f"{md_line('Generated At', latest_alert.get('generated_at'))}\n\n"
        "*Family Anomaly*\n"
        f"{md_line('Family Count', latest_report.get('family_count'))}\n"
        f"{md_line('Market Count', latest_report.get('market_count'))}\n"
        f"{md_line('Top Family', _top_family(latest_report))}\n"
        f"{md_line('Top Score', _top_score(latest_report))}\n"
        f"{md_line('Top Bucket', _top_bucket(latest_report, latest_anomaly))}\n"
        f"{md_line('Signal Summary', _format_signal_summary(latest_report.get('signal_summary')))}\n"
        f"{md_line('Bucket Counts', _format_bucket_counts(latest_report.get('anomaly_bucket_counts')))}\n"
        f"{md_line('Latest Anomaly Market', latest_anomaly.get('market_id'))}\n"
        f"{md_line('Latest Anomaly Reason', latest_anomaly.get('primary_reason'))}\n"
        f"{md_line('Governance', latest_anomaly.get('governance_reason'))}\n"
        f"{md_line('Generated At', latest_report.get('generated_at'))}\n\n"
        "*Scanner Status*\n"
        f"{md_line('Total Markets', latest_scanner_status.get('total_markets'))}\n"
        f"{md_line('Scanned Markets', latest_scanner_status.get('scanned_markets'))}\n"
        f"{md_line('Fresh / Stale / Unavailable', scan_ratio)}\n"
        f"{md_line('Freshness Mix', latest_scanner_status.get('freshness_counts'))}\n"
        f"{md_line('Priority Mix', latest_scanner_status.get('priority_counts'))}\n"
        f"{md_line('Alert Markets', latest_scanner_status.get('alert_markets'))}\n"
        f"{md_line('Backlog', latest_scanner_status.get('backlog_count'))}\n"
        f"{md_line('Next Scan ETA', latest_scanner_status.get('next_scan_eta'))}\n"
        f"{md_line('Universe Markets', latest_market_universe.get('market_count'))}\n"
        f"{md_line('Evidence Rows', latest_evidence_scan.get('market_count'))}\n"
        f"{md_line('Queue Accepted / Suppressed', queue_ratio)}\n\n"
        "*Operator Summary*\n"
        f"{md_line('Summary', operator_summary.get('summary_line'))}\n"
        f"{md_line('Focus Market', operator_summary.get('current_focus'))}\n"
        f"{md_line('Focus Family', operator_summary.get('current_family'))}\n"
        f"{md_line('Alert Severity', operator_summary.get('alert_severity'))}\n"
        f"{md_line('Anomaly Bucket', operator_summary.get('anomaly_bucket'))}\n"
        f"{md_line('Scanner Freshness', operator_summary.get('scanner_freshness'))}\n"
        f"{md_line('Priority Mix', operator_summary.get('priority_mix'))}\n"
        f"{md_line('Gate Status', operator_summary.get('gate_status'))}\n"
        f"{md_line('Recommended Action', operator_summary.get('recommended_operator_action'))}\n"
        f"{md_line('Next Step', operator_summary.get('next_step'))}\n"
        f"{md_line('Primary Reason', operator_summary.get('primary_reason'))}\n\n"
        "*Gate / Runtime Block*\n"
        f"{md_line('Overall', runtime_block.get('overall_status'))}\n"
        f"{md_line('Gate Status', runtime_block.get('gate_status'))}\n"
        f"{md_line('Execution Status', runtime_block.get('execution_status'))}\n"
        f"{md_line('Ready For Live', runtime_block.get('ready_for_live'))}\n"
        f"{md_line('Can Execute', runtime_block.get('can_execute'))}\n"
        f"{md_line('Primary Block Reason', runtime_block.get('primary_block_reason'))}\n"
        f"{md_line('Recommended Action', runtime_block.get('recommended_operator_action'))}\n"
        f"{md_line('Block Count', runtime_block.get('block_reason_count'))}\n"
        f"{md_line('Generated At', latest_source_policy.get('generated_at') or latest_alert.get('generated_at') or latest_anomaly.get('generated_at'))}\n\n"
        "*Latest Anomaly Event*\n"
        f"{md_line('Market', latest_anomaly.get('market_id'))}\n"
        f"{md_line('Family', latest_anomaly.get('market_family'))}\n"
        f"{md_line('Score', latest_anomaly.get('anomaly_score'))}\n"
        f"{md_line('Intervention Like', latest_anomaly.get('intervention_like_score'))}\n"
        f"{md_line('Reason', latest_anomaly.get('primary_reason'))}\n"
        f"{md_line('Generated At', latest_anomaly.get('generated_at'))}\n"
        "\n*Source Policy*\n"
        f"{md_line('Overall', latest_source_policy.get('overall_status'))}\n"
        f"{md_line('Fresh', (latest_source_policy.get('counts') or {}).get('fresh'))}\n"
        f"{md_line('Stale', (latest_source_policy.get('counts') or {}).get('stale'))}\n"
        f"{md_line('Unavailable', (latest_source_policy.get('counts') or {}).get('unavailable'))}\n"
        f"{md_line('Priority Mix', latest_source_policy.get('priority_counts'))}\n"
        f"{md_line('Fallback Policies', _summarize_policy_fallbacks(latest_source_policy.get('sources') or []))}\n"
        f"{md_line('Problem Sources', _summarize_policy_issues(latest_source_policy.get('problem_sources') or []))}\n"
        "\n*Monitoring Trend*\n"
        f"{md_line('Window', trend.get('window'))}\n"
        f"{md_line('Severities', severity_counts)}\n"
        f"{md_line('Recent Alerts', _summarize_alerts(recent_alerts))}\n"
        f"{md_line('Recent Anomalies', _summarize_anomalies(recent_anomalies))}\n"
    )


def _top_family(report: dict) -> object:
    summaries = report.get("family_summaries") or []
    if not summaries:
        return "-"
    ranked = sorted(
        (summary for summary in summaries if isinstance(summary, dict)),
        key=lambda item: float(item.get("max_intervention_like_score") or 0.0),
        reverse=True,
    )
    return ranked[0].get("market_family") if ranked else "-"


def _top_score(report: dict) -> object:
    summaries = report.get("family_summaries") or []
    if not summaries:
        return "-"
    ranked = sorted(
        (summary for summary in summaries if isinstance(summary, dict)),
        key=lambda item: float(item.get("max_intervention_like_score") or 0.0),
        reverse=True,
    )
    return ranked[0].get("max_intervention_like_score") if ranked else "-"


def _top_bucket(report: dict, latest_anomaly: dict) -> object:
    if latest_anomaly.get("anomaly_bucket"):
        return latest_anomaly.get("anomaly_bucket")
    summaries = report.get("family_summaries") or []
    if not summaries:
        return "-"
    ranked = sorted(
        (summary for summary in summaries if isinstance(summary, dict)),
        key=lambda item: float(item.get("max_intervention_like_score") or 0.0),
        reverse=True,
    )
    if not ranked:
        return "-"
    return _bucket_for_score(ranked[0].get("max_intervention_like_score"))


def _bucket_for_score(score: object) -> str:
    try:
        value = float(score or 0.0)
    except (TypeError, ValueError):
        value = 0.0
    if value >= 0.8:
        return "high"
    if value >= 0.5:
        return "medium"
    return "low"


def _format_signal_summary(summary: object) -> str:
    if not isinstance(summary, dict) or not summary:
        return "-"
    return (
        f"pv={summary.get('price_velocity_high_count', 0)} "
        f"edge={summary.get('edge_dislocation_high_count', 0)} "
        f"mismatch={summary.get('evidence_mismatch_count', 0)} "
        f"stress={summary.get('microstructure_stress_high_count', 0)} "
        f"peer={summary.get('peer_outlier_count', 0)} "
        f"high={summary.get('intervention_like_high_count', 0)}"
    )


def _format_bucket_counts(counts: object) -> str:
    if not isinstance(counts, dict) or not counts:
        return "-"
    return (
        f"high={counts.get('high', 0)} "
        f"medium={counts.get('medium', 0)} "
        f"low={counts.get('low', 0)}"
    )


def _summarize_alerts(alerts: list[dict]) -> str:
    if not alerts:
        return "-"
    parts = []
    for alert in alerts[:3]:
        if not isinstance(alert, dict):
            continue
        parts.append(
            f"{alert.get('market_id', '-')}:"
            f"{alert.get('severity', '-')}/"
            f"{alert.get('primary_reason', '-')}"
        )
    return " | ".join(parts) or "-"


def _summarize_anomalies(anomalies: list[dict]) -> str:
    if not anomalies:
        return "-"
    parts = []
    for anomaly in anomalies[:3]:
        if not isinstance(anomaly, dict):
            continue
        parts.append(
            f"{anomaly.get('market_id', '-')}:"
            f"{anomaly.get('anomaly_score', '-')}/"
            f"{anomaly.get('primary_reason', '-')}"
        )
    return " | ".join(parts) or "-"


def _summarize_policy_issues(sources: list[dict]) -> str:
    if not sources:
        return "-"
    parts = []
    for source in sources[:3]:
        if not isinstance(source, dict):
            continue
        parts.append(
            f"{source.get('source_name', '-')}:"
            f"{source.get('freshness_status', '-')}/"
            f"{source.get('status_reason', '-')}"
        )
    return " | ".join(parts) or "-"


def _summarize_policy_fallbacks(sources: list[dict]) -> str:
    if not sources:
        return "-"
    parts = []
    for source in sources[:3]:
        if not isinstance(source, dict):
            continue
        parts.append(
            f"{source.get('source_name', '-')}:"
            f"{source.get('priority_level', '-')}/"
            f"{source.get('fallback_policy', '-')}"
        )
    return " | ".join(parts) or "-"
