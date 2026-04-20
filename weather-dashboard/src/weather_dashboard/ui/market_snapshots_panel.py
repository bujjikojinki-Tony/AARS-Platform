from __future__ import annotations

from datetime import datetime, timezone
from html import escape

import pandas as pd
import streamlit as st

from weather_dashboard.ui.compact_panel import render_panel_title, sanitize_text


def _parse_dt(value: object) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _build_frame(market_snapshots: list[dict], pinned_market_id: str | None) -> pd.DataFrame:
    rows = []
    now = datetime.now(timezone.utc)

    for snapshot in market_snapshots:
        updated_at = _parse_dt(snapshot.get("updated_at"))
        age_minutes = None
        if updated_at is not None:
            age_minutes = max((now - updated_at).total_seconds() / 60.0, 0.0)

        rows.append(
            {
                "pinned": bool(
                    pinned_market_id and str(snapshot.get("market_id")) == pinned_market_id
                ),
                "market_id": snapshot.get("market_id"),
                "market_family": snapshot.get("market_family"),
                "market_question": snapshot.get("market_question"),
                "updated_at": snapshot.get("updated_at"),
                "age_min": round(age_minutes, 1) if age_minutes is not None else None,
                "favored_side": snapshot.get("favored_side"),
                "market_probability": snapshot.get("market_probability"),
                "market_band_scheme": snapshot.get("market_band_scheme"),
                "market_band": snapshot.get("market_band"),
                "location_name": snapshot.get("location_name"),
                "market_band_label": snapshot.get("market_band_label"),
                "resolver_status": snapshot.get("resolver_status") or "unknown",
                "edge_bucket": snapshot.get("edge_bucket") or "unknown",
                "freshness_bucket": snapshot.get("freshness_bucket") or "unknown",
                "confidence_adjusted_edge": snapshot.get("confidence_adjusted_edge"),
                "search_source": snapshot.get("search_source") or snapshot.get("source") or "live",
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(by=["pinned", "updated_at"], ascending=[False, False])
    return df


def filter_market_watchlist_frame(
    frame: pd.DataFrame,
    *,
    query: str,
    family: str,
    resolver_status: str,
    edge_bucket: str,
    freshness_bucket: str,
) -> pd.DataFrame:
    working = frame.copy()
    if family != "All":
        working = working[working["market_family"].astype(str) == family]
    if resolver_status != "All":
        working = working[working["resolver_status"].astype(str) == resolver_status]
    if edge_bucket != "All":
        working = working[working["edge_bucket"].astype(str) == edge_bucket]
    if freshness_bucket != "All":
        working = working[working["freshness_bucket"].astype(str) == freshness_bucket]
    if query.strip():
        needle = query.strip().lower()
        haystack = working.fillna("").astype(str).agg(" ".join, axis=1).str.lower()
        working = working[haystack.str.contains(needle, regex=False)]
    return working


def _style_watchlist(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    def highlight_row(row: pd.Series) -> list[str]:
        is_pinned = bool(row.get("pinned"))
        age_minutes = row.get("age_min")
        styles = []
        for _ in row.index:
            if is_pinned:
                styles.append("background-color: rgba(255, 193, 7, 0.16); font-weight: 600;")
            elif age_minutes is not None and age_minutes <= 5:
                styles.append("background-color: rgba(25, 135, 84, 0.08);")
            else:
                styles.append("")
        return styles

    return df.style.apply(highlight_row, axis=1)


def _render_watchlist_card(
    row: dict,
    idx: int,
    pinned_market_id: str | None,
    removable_market_ids: set[str],
) -> dict | None:
    market_id = str(row.get("market_id") or "")
    if not market_id:
        return None

    question = str(row.get("market_question") or market_id)
    family = str(row.get("market_family") or "unknown")
    source = "manual" if market_id in removable_market_ids else str(row.get("search_source") or "live")
    is_pinned = bool(pinned_market_id and str(pinned_market_id) == market_id)
    age = row.get("age_min")
    age_label = f"{age:.1f}m" if isinstance(age, (int, float)) else "-"
    probability = row.get("market_probability")
    probability_label = f"{float(probability):.2f}" if isinstance(probability, (int, float)) else "-"
    band = str(row.get("market_band") or "-")
    side = str(row.get("favored_side") or "-")

    card_class = "watchlist-card watchlist-card--pinned" if is_pinned else "watchlist-card"
    st.markdown(
        (
            f"<div class='{card_class}'>"
            "<div class='watchlist-card-top'>"
            f"<span class='watchlist-source'>{escape(sanitize_text(source.upper()))}</span>"
            f"<span class='watchlist-age'>updated {escape(sanitize_text(age_label))} ago</span>"
            "</div>"
            f"<div class='watchlist-question'>{escape(sanitize_text(question))}</div>"
            "<div class='watchlist-meta-row'>"
            f"<span>{escape(sanitize_text(market_id))}</span>"
            f"<span>{escape(sanitize_text(family))}</span>"
            f"<span>side {escape(sanitize_text(side))}</span>"
            f"<span>p {escape(sanitize_text(probability_label))}</span>"
            f"<span>band {escape(sanitize_text(band))}</span>"
            "</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns([0.9, 0.9, 0.9, 1.0])
    with c1:
        if st.button(
            "Focus",
            key=f"watchlist_focus_{idx}_{market_id}",
            use_container_width=True,
        ):
            return {"action": "focus", "market_id": market_id}
    with c2:
        if is_pinned:
            if st.button(
                "Unpin",
                key=f"watchlist_unpin_{idx}_{market_id}",
                use_container_width=True,
            ):
                return {"action": "unpin", "market_id": market_id}
        elif st.button(
            "Pin",
            key=f"watchlist_pin_{idx}_{market_id}",
            use_container_width=True,
        ):
            return {"action": "pin", "market_id": market_id}
    with c3:
        if st.button(
            "Remove",
            key=f"watchlist_remove_{idx}_{market_id}",
            use_container_width=True,
        ):
            return {"action": "remove", "market_id": market_id}
    with c4:
        st.caption("Pinned" if is_pinned else "Tracked")

    return None


def render_market_snapshots_panel(
    market_snapshots: list[dict],
    pinned_market_id: str | None,
    removable_market_ids: set[str] | None = None,
) -> dict | None:
    render_panel_title("Market Watchlist")

    if not market_snapshots:
        st.info("No market snapshots found.")
        return None

    frame = _build_frame(market_snapshots, pinned_market_id)
    if frame.empty:
        st.info("No market snapshots found.")
        return None

    removable_market_ids = removable_market_ids or set()
    selected_action = None

    filter_cols = st.columns([1.15, 0.7, 0.7, 0.7, 0.7])
    with filter_cols[0]:
        query = st.text_input(
            "Filter watchlist",
            value="",
            placeholder="Filter by market, id, family, location, band...",
            key="market_watchlist_filter",
        )
    with filter_cols[1]:
        family_options = ["All"] + sorted(
            str(family)
            for family in frame["market_family"].dropna().unique().tolist()
            if str(family)
        )
        selected_family = st.selectbox(
            "Family",
            family_options,
            key="market_watchlist_family_filter",
        )
    with filter_cols[2]:
        resolver_options = ["All"] + sorted(
            str(value)
            for value in frame["resolver_status"].dropna().unique().tolist()
            if str(value)
        )
        selected_resolver_status = st.selectbox(
            "Resolver",
            resolver_options,
            key="market_watchlist_resolver_filter",
        )
    with filter_cols[3]:
        edge_options = ["All"] + sorted(
            str(value)
            for value in frame["edge_bucket"].dropna().unique().tolist()
            if str(value)
        )
        selected_edge_bucket = st.selectbox(
            "Edge",
            edge_options,
            key="market_watchlist_edge_filter",
        )
    with filter_cols[4]:
        freshness_options = ["All"] + sorted(
            str(value)
            for value in frame["freshness_bucket"].dropna().unique().tolist()
            if str(value)
        )
        selected_freshness_bucket = st.selectbox(
            "Freshness",
            freshness_options,
            key="market_watchlist_freshness_filter",
        )

    working = filter_market_watchlist_frame(
        frame,
        query=query,
        family=selected_family,
        resolver_status=selected_resolver_status,
        edge_bucket=selected_edge_bucket,
        freshness_bucket=selected_freshness_bucket,
    )

    st.caption(
        f"{len(working)} visible / {len(frame)} tracked. "
        "Filter by family, resolver, edge and freshness to turn the watchlist into a trading desk."
    )

    if working.empty:
        st.info("No watchlist markets match the current filter.")
        return None

    st.markdown(
        """
        <style>
        .watchlist-card {
            margin-top: 0.38rem;
            padding: 0.58rem 0.68rem;
            border: 1px solid rgba(35, 72, 82, 0.14);
            border-radius: 14px;
            background: linear-gradient(180deg, rgba(255,255,255,0.94), rgba(248,246,239,0.86));
            box-shadow: 0 8px 22px rgba(49, 77, 75, 0.06);
        }
        .watchlist-card--pinned {
            border-color: rgba(196, 122, 21, 0.42);
            background: linear-gradient(180deg, rgba(255,249,229,0.98), rgba(253,241,205,0.82));
        }
        .watchlist-card-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.65rem;
            margin-bottom: 0.26rem;
        }
        .watchlist-source {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            background: rgba(20, 82, 72, 0.10);
            color: #145248;
            padding: 0.12rem 0.46rem;
            font-family: "SF Mono", "Menlo", monospace;
            font-size: 0.58rem;
            font-weight: 900;
            letter-spacing: 0.08em;
        }
        .watchlist-age {
            color: #667782;
            font-size: 0.66rem;
            font-weight: 750;
        }
        .watchlist-question {
            color: #17252b;
            font-family: "Avenir Next", "Trebuchet MS", sans-serif;
            font-size: 0.86rem;
            font-weight: 850;
            line-height: 1.18;
        }
        .watchlist-meta-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.36rem;
            margin-top: 0.34rem;
        }
        .watchlist-meta-row span {
            border: 1px solid rgba(35, 72, 82, 0.12);
            border-radius: 999px;
            color: #667782;
            background: rgba(255,255,255,0.58);
            padding: 0.08rem 0.4rem;
            font-size: 0.63rem;
            line-height: 1.2;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    working["market_family"] = working["market_family"].fillna("unknown")
    families = [family for family in working["market_family"].unique().tolist()]
    for family in families:
        family_df = working[working["market_family"] == family].copy()
        pinned_count = int(family_df["pinned"].sum()) if "pinned" in family_df.columns else 0
        latest_updated_at = family_df["updated_at"].iloc[0] if not family_df.empty else "-"
        header = f"{family} • {len(family_df)} markets"
        if pinned_count:
            header += " • pinned"
        with st.expander(header, expanded=(pinned_count > 0)):
            left, right = st.columns([2, 1])
            with left:
                st.markdown(f"**Latest update:** `{latest_updated_at}`")
            with right:
                st.markdown(f"**Pinned in group:** `{pinned_count}`")

            st.caption("Focus switches the desk to that market. Pin persists it across refreshes. Remove hides it from the watchlist.")
            for idx, row in enumerate(family_df.to_dict("records")):
                action = _render_watchlist_card(
                    row,
                    idx=idx,
                    pinned_market_id=pinned_market_id,
                    removable_market_ids=removable_market_ids,
                )
                if action is not None:
                    selected_action = action

    return selected_action
