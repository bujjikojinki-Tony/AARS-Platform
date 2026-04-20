from __future__ import annotations

from datetime import datetime, timezone
import json

import streamlit as st

from weather_dashboard.ui.compact_panel import render_panel_title, sanitize_text
from weather_dashboard.settings import PINNED_MARKET_OVERRIDE_JSON


def _parse_dt(value: object) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _pin_recent_market(item: dict) -> None:
    market_id = str(item.get("market_id") or "")
    label = str(item.get("market_question") or item.get("market_id") or "-")
    source = str(item.get("source") or "recent")

    st.session_state["pinned_market_override"] = market_id
    st.session_state["pinned_market_override_label"] = label
    st.session_state["pinned_market_override_source"] = source
    st.session_state["pinned_market_override_snapshot"] = {
        "market_id": market_id,
        "market_question": label,
        "market_family": item.get("market_family"),
        "updated_at": item.get("chosen_at"),
        "search_source": source,
    }
    PINNED_MARKET_OVERRIDE_JSON.parent.mkdir(parents=True, exist_ok=True)
    PINNED_MARKET_OVERRIDE_JSON.write_text(
        json.dumps(
            {
                "market_id": market_id,
                "label": label,
                "source": source,
                "snapshot": st.session_state["pinned_market_override_snapshot"],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _clear_recent_pin() -> None:
    for key in (
        "pinned_market_override",
        "pinned_market_override_label",
        "pinned_market_override_source",
        "pinned_market_override_snapshot",
    ):
        st.session_state.pop(key, None)
    if PINNED_MARKET_OVERRIDE_JSON.exists():
        PINNED_MARKET_OVERRIDE_JSON.unlink()


def render_recent_markets_panel(recent_markets: list[dict]) -> None:
    render_panel_title("Recent Markets")

    if not recent_markets:
        st.info("No recent market selections yet.")
        return

    now = datetime.now(timezone.utc)

    st.caption(
        "Recent selections are logged with their source so you can track how the desk moved."
    )

    rows = []
    for item in recent_markets:
        chosen_at = _parse_dt(item.get("chosen_at"))
        age_minutes = None
        if chosen_at is not None:
            age_minutes = max((now - chosen_at.astimezone(timezone.utc)).total_seconds() / 60.0, 0.0)

        rows.append(
            {
                "chosen_at": chosen_at,
                "chosen_at_ts": int(item.get("chosen_at_ts") or (chosen_at.timestamp() if chosen_at else 0)),
                "age_min": age_minutes,
                "source": item.get("source", "-"),
                "market_id": item.get("market_id", "-"),
                "market_family": item.get("market_family", "-"),
                "market_question": item.get("label", "-"),
            }
        )

    rows.sort(key=lambda row: int(row.get("chosen_at_ts") or 0), reverse=True)

    for idx, item in enumerate(rows):
        age_text = f"{item['age_min']:.1f}m ago" if item["age_min"] is not None else "time unknown"
        source = str(item.get("source", "-")).lower()
        current_pinned_market = str(st.session_state.get("pinned_market_override") or "")
        is_pinned = bool(current_pinned_market and current_pinned_market == str(item.get("market_id") or ""))
        pin_label = "Unpin" if is_pinned else "Pin"
        with st.container(border=True):
            left, right = st.columns([3, 1], vertical_alignment="top")
            with left:
                st.caption(sanitize_text(item.get("market_family") or "unknown").upper())
                st.markdown(f"**{sanitize_text(item.get('market_question') or '-')}**")
                st.caption(sanitize_text(item.get("market_id") or "-"))
            with right:
                st.metric("Source", sanitize_text(source.upper()))
                st.caption(sanitize_text(age_text))
                st.caption(f"selected {sanitize_text(item.get('chosen_at').isoformat() if item.get('chosen_at') else '-')}")
                if st.button(
                    pin_label,
                    key=f"recent_pin_{idx}_{item.get('market_id')}",
                    use_container_width=True,
                ):
                    if is_pinned:
                        _clear_recent_pin()
                    else:
                        _pin_recent_market(item)
                    st.rerun()
