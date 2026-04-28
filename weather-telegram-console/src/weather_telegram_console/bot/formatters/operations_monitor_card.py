from __future__ import annotations

from weather_telegram_console.bot.formatters.telegram_text import md_line


def format_operations_monitor_card(payload: dict) -> str:
    global_summary = payload.get("global_summary") or {}
    focus_markets = payload.get("focus_markets") or []
    system_health = payload.get("system_health") or {}
    scanner_health = system_health.get("scanner_health") or {}
    source_health = system_health.get("source_health") or {}
    queue_health = system_health.get("queue_health") or {}
    family_health = system_health.get("family_scan_health") or {}
    selected_detail = payload.get("selected_market_quick_detail") or {}
    ops_alerts = payload.get("ops_alerts") or []
    summary = payload.get("summary") or {}

    return (
        "*AARS Operations Monitor*\n"
        f"{md_line('Markets Scanned', global_summary.get('markets_scanned'))}\n"
        f"{md_line('Focus Markets', global_summary.get('focus_markets_count'))}\n"
        f"{md_line('Fresh Ratio', global_summary.get('fresh_ratio'))}\n"
        f"{md_line('Alert Markets', global_summary.get('high_alert_markets'))}\n"
        f"{md_line('Gate Blocked', global_summary.get('gate_blocked_markets'))}\n"
        f"{md_line('Ops Alerts', global_summary.get('ops_alert_count'))}\n\n"
        "*Focus Markets*\n"
        f"{md_line('Top Focus', _summarize_focus_markets(focus_markets))}\n\n"
        "*Scanner Health*\n"
        f"{md_line('Status', scanner_health.get('status'))}\n"
        f"{md_line('Scanned Markets', scanner_health.get('scanned_markets'))}\n"
        f"{md_line('Fresh Markets', scanner_health.get('fresh_markets'))}\n"
        f"{md_line('Stale Markets', scanner_health.get('stale_markets'))}\n"
        f"{md_line('Unavailable Markets', scanner_health.get('unavailable_markets'))}\n"
        f"{md_line('Backlog', scanner_health.get('backlog_count'))}\n"
        f"{md_line('Next Scan ETA', scanner_health.get('next_scan_eta'))}\n"
        f"{md_line('Priority Counts', scanner_health.get('priority_counts'))}\n"
        f"{md_line('Freshness Counts', scanner_health.get('freshness_counts'))}\n\n"
        "*Source Health*\n"
        f"{md_line('Overall Status', source_health.get('overall_status'))}\n"
        f"{md_line('Counts', source_health.get('counts'))}\n"
        f"{md_line('Problem Sources', _summarize_problem_sources(source_health.get('problem_sources') or []))}\n\n"
        "*Queue / Family*\n"
        f"{md_line('Accepted', queue_health.get('accepted_count'))}\n"
        f"{md_line('Suppressed', queue_health.get('suppressed_count'))}\n"
        f"{md_line('Family', family_health.get('market_family'))}\n"
        f"{md_line('Family Summary', family_health.get('family_risk_summary'))}\n\n"
        "*Selected Market*\n"
        f"{md_line('Market', selected_detail.get('market_id'))}\n"
        f"{md_line('Question', selected_detail.get('market_question'))}\n"
        f"{md_line('Action', selected_detail.get('recommended_operator_action'))}\n"
        f"{md_line('Boundary', selected_detail.get('execution_boundary'))}\n\n"
        "*Latest Ops Alerts*\n"
        f"{md_line('Alerts', _summarize_ops_alerts(ops_alerts))}\n"
        f"{md_line('Primary Warning', summary.get('primary_warning'))}\n"
    )


def _summarize_focus_markets(focus_markets: list[dict]) -> str:
    if not focus_markets:
        return "-"
    parts = []
    for market in focus_markets[:4]:
        if not isinstance(market, dict):
            continue
        parts.append(
            f"{market.get('city', '-')}/{market.get('market_family', '-')}"
            f"#{market.get('focus_reason', '-')}"
        )
    return " | ".join(parts) or "-"


def _summarize_problem_sources(problem_sources: list[dict]) -> str:
    if not problem_sources:
        return "-"
    parts = []
    for source in problem_sources[:4]:
        if not isinstance(source, dict):
            continue
        parts.append(
            f"{source.get('source_name', '-')}:"
            f"{source.get('freshness_status', '-')}/"
            f"{source.get('status_reason', '-')}"
        )
    return " | ".join(parts) or "-"


def _summarize_ops_alerts(ops_alerts: list[dict]) -> str:
    if not ops_alerts:
        return "-"
    parts = []
    for alert in ops_alerts[:4]:
        if not isinstance(alert, dict):
            continue
        parts.append(
            f"{alert.get('component', '-')}:"
            f"{alert.get('severity', '-')}/"
            f"{alert.get('primary_reason', '-')}"
        )
    return " | ".join(parts) or "-"
