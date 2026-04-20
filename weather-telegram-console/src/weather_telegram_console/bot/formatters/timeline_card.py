from __future__ import annotations


def format_timeline_card(market_id: str, entries: list[dict]) -> str:
    lines = [
        "*AARS Market Timeline*",
        f"*Market ID:* `{market_id}`",
        "",
    ]
    for index, entry in enumerate(entries, start=1):
        lines.append(
            f"{index}. `{entry.get('timestamp', '-')}` "
            f"`{entry.get('comparison_status', '-')}` "
            f"hint=`{entry.get('action_hint', '-')}` "
            f"market=`{entry.get('market_band', '-')}` "
            f"model=`{entry.get('model_band', '-')}` "
            f"value=`{entry.get('model_value', '-')}` "
            f"gap=`{entry.get('confidence_adjusted_gap', '-')}` "
            f"conf=`{entry.get('confidence_score', '-')}` "
            f"m_ref=`{entry.get('market_snapshot_ref', '-')}` "
            f"f_ref=`{entry.get('forecast_snapshot_ref', '-')}`"
        )
    return "\n".join(lines)
