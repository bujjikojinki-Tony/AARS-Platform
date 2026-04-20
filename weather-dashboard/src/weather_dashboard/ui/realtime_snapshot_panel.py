from __future__ import annotations

import pandas as pd
import streamlit as st


def render_realtime_snapshot_panel(snapshot_payload: dict | None) -> None:
    st.subheader("Polymarket Realtime Snapshot")

    if not snapshot_payload:
        st.info("No realtime snapshot available.")
        return

    updated_at = snapshot_payload.get("updated_at", "-")
    asset_count = snapshot_payload.get("asset_count", 0)
    states = snapshot_payload.get("states") or []

    c1, c2 = st.columns(2)
    c1.metric("Asset Count", asset_count)
    c2.metric("Updated At", updated_at)

    if not states:
        st.info("No asset states in realtime snapshot.")
        return

    df = pd.DataFrame(states)
    display_cols = [
        "asset_id",
        "updated_at",
        "event_type",
        "best_bid",
        "best_ask",
        "last_trade_price",
    ]
    existing = [c for c in display_cols if c in df.columns]
    st.dataframe(df[existing], use_container_width=True, hide_index=True)
