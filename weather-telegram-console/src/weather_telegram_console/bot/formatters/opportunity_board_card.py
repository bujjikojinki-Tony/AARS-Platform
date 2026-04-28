from __future__ import annotations

from weather_telegram_console.bot.formatters.telegram_text import md_line
from weather_telegram_console.bot.formatters.telegram_text import safe_text


def format_opportunity_board_card(payload: dict) -> str:
    summary = payload.get("summary") or {}
    rows = payload.get("rows") or []
    selected_city = payload.get("selected_city") or payload.get("city") or "-"
    family_anomaly = payload.get("family_anomaly_summary") or {}
    lines = [
        "*AARS Opportunity Board*",
        f"{md_line('Rows', payload.get('row_count'))}",
        f"{md_line('Selected City', selected_city)}",
        f"{md_line('Cities', summary.get('city_count'))}",
        f"{md_line('Families', summary.get('family_count'))}",
        f"{md_line('High Opp', summary.get('high_opportunity_count'))}",
        f"{md_line('Top Model', summary.get('top_model'))}",
        f"{md_line('Top Action', summary.get('top_action'))}",
        f"{md_line('Family Scan Status', family_anomaly.get('family_scan_status'))}",
        f"{md_line('Top Scan Family', family_anomaly.get('top_family'))}",
        f"{md_line('Top Scan Score', family_anomaly.get('top_score'))}",
        f"{md_line('Top Scan Bucket', family_anomaly.get('top_bucket'))}",
        "",
        "*Top Opportunities*",
    ]
    for row in rows[:5]:
        if not isinstance(row, dict):
            continue
        lines.extend(
            [
                f"{md_line('City', row.get('city'))}",
                f"{md_line('Family', row.get('market_family'))}",
                f"{md_line('Opp', row.get('opportunity_score'))}",
                f"{md_line('Diff', row.get('difficulty_label') or row.get('difficulty_score'))}",
                f"{md_line('Model', row.get('best_model'))}",
                f"{md_line('Alerts', row.get('alert_count'))}",
                f"{md_line('Anomalies', row.get('anomaly_count'))}",
                f"{md_line('Action', row.get('recommended_action'))}",
                f"{md_line('Gate Risk', row.get('gate_risk_summary'))}",
                f"{md_line('Seed Prior', _seed_hint(row))}",
                f"{md_line('Open Market', _market_hint(row))}",
                "",
            ]
        )
    if not rows:
        lines.append("-")
    elif selected_city not in {"-", ""}:
        top_row = rows[0]
        lines.extend(
            [
                "*City Detail*",
                f"{md_line('Top Family', top_row.get('market_family'))}",
                f"{md_line('Best Model', top_row.get('best_model'))}",
                f"{md_line('Latest Alert', top_row.get('latest_alert_severity'))}",
                f"{md_line('Latest Anomaly', top_row.get('latest_anomaly_score'))}",
                f"{md_line('Next Step', _next_step(top_row))}",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def _market_hint(row: dict) -> str:
    refs = row.get("upstream_refs") or {}
    market_ids = refs.get("market_ids") or []
    market_id = market_ids[0] if market_ids else "-"
    return f"/market {safe_text(market_id)}" if market_id not in {"-", ""} else "-"


def _seed_hint(row: dict) -> str:
    if not row.get("seeded_from_manual_research"):
        return "-"
    origin = safe_text(row.get("source_origin") or "manual_research")
    confidence = safe_text(row.get("manual_confidence") or "-")
    return f"{origin}; confidence={confidence}"


def _next_step(row: dict) -> str:
    action = safe_text(row.get("recommended_action"))
    market_hint = _market_hint(row)
    if market_hint != "-":
        return f"{action}; then {market_hint}"
    return action
