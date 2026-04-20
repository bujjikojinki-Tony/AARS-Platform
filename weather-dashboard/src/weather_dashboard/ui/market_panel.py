from __future__ import annotations

import streamlit as st


def render_market_panel(market_bundles: list[dict]) -> None:
    st.subheader("Latest Market Bundles")

    if not market_bundles:
        st.info("No market bundles found.")
        return

    for i, bundle in enumerate(market_bundles[:3], start=1):
        market = bundle.get("market") or {}
        price_state = bundle.get("price_state") or {}

        title = market.get("market_question") or market.get("event_title") or f"Market Bundle #{i}"
        with st.expander(title, expanded=(i == 1)):
            c1, c2, c3 = st.columns(3)

            with c1:
                st.markdown(f"**Market ID:** `{market.get('market_id', '-')}`")
                st.markdown(f"**Location:** {market.get('location_name', '-')}")
                st.markdown(f"**Category:** {market.get('category', '-')}")

            with c2:
                st.markdown(f"**Active:** {market.get('active', '-')}")
                st.markdown(f"**Closed:** {market.get('closed', '-')}")
                st.markdown(f"**Volume 24h:** {market.get('volume_24hr', '-')}")

            with c3:
                st.markdown(f"**Favored Outcome:** {price_state.get('favored_outcome', '-')}")
                st.markdown(f"**Favored Probability:** {price_state.get('favored_probability', '-')}")
                st.markdown(f"**Implied Band:** {price_state.get('implied_band', '-')}")

            st.json(bundle)
