import streamlit as st


def render_raw_json_panel(
    signal_payload: dict,
    market_bundles: list[dict],
    market_snapshots: list[dict] | None = None,
    rulebook_payload: dict | None = None,
) -> None:
    st.subheader("Raw JSON Drill-down")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Signal JSON", "Market Bundle JSON", "Market Snapshots JSON", "Rulebook JSON"]
    )

    with tab1:
        if signal_payload:
            st.json(signal_payload)
        else:
            st.info("No signal payload available.")

    with tab2:
        if market_bundles:
            st.json(market_bundles)
        else:
            st.info("No market bundles available.")

    with tab3:
        if market_snapshots:
            st.json(market_snapshots)
        else:
            st.info("No market snapshots available.")

    with tab4:
        if rulebook_payload:
            st.json(rulebook_payload)
        else:
            st.info("No rulebook payload available.")
