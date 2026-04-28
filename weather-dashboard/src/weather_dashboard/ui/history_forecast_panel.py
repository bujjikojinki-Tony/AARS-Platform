from __future__ import annotations

import streamlit as st

from weather_dashboard.ui.compact_panel import sanitize_text


def _is_shanghai_market(snapshot: dict | None) -> bool:
    if not snapshot:
        return False
    market_id = str(snapshot.get("market_id") or "")
    location_name = str(snapshot.get("location_name") or "")
    question = str(snapshot.get("market_question") or "")
    return (
        market_id == "sample_market_shanghai_001"
        or location_name.lower() == "shanghai"
        or "shanghai" in question.lower()
    )


def render_history_forecast_panel(
    selected_market_snapshot: dict | None,
    realtime_forecast: dict | None,
    shanghai_history_reference: dict | None,
    shanghai_live_weather: dict | None,
) -> None:
    st.subheader("Historical Data / Future Forecast")

    left, right = st.columns(2)

    with left:
        st.markdown("### Historical Data")
        if _is_shanghai_market(selected_market_snapshot) and shanghai_live_weather:
            if shanghai_live_weather.get("fetched_at"):
                st.caption(
                    f"Cached ZSPD snapshot fetched at: {sanitize_text(shanghai_live_weather.get('fetched_at'))}"
                )
            st.markdown(f"**Observed At:** {sanitize_text(shanghai_live_weather.get('observed_valid_time', '-'))}")
            st.markdown(f"**Observed Temperature:** {sanitize_text(shanghai_live_weather.get('observed_temp_c', '-'))}")
            st.markdown(f"**Observed Max 24h:** {sanitize_text(shanghai_live_weather.get('observed_temp_max_24h_c', '-'))}")
            st.markdown(f"**Observed Min 24h:** {sanitize_text(shanghai_live_weather.get('observed_temp_min_24h_c', '-'))}")
            st.markdown(
                f"**Settlement Source:** [Wunderground ZSPD]({sanitize_text(shanghai_live_weather.get('history_url'))})"
            )
            st.caption("This is live observed station data from Shanghai Pudong, not a mock sample.")
        elif realtime_forecast and realtime_forecast.get("station_history_url"):
            st.markdown("**Station History Source:**")
            st.markdown(
                f"[Historical Station Page]({sanitize_text(realtime_forecast.get('station_history_url'))})"
            )
            st.caption("A direct historical settlement row has not been materialized for this market yet.")
        else:
            st.info("No historical station data is available for the selected market yet.")

    with right:
        st.markdown("### Future Forecast")
        if _is_shanghai_market(selected_market_snapshot) and shanghai_live_weather:
            st.markdown(
                f"**Forecast Target Date:** {sanitize_text(shanghai_live_weather.get('forecast_target_date', '-'))}"
            )
            st.markdown(
                f"**Forecast Max:** {sanitize_text(shanghai_live_weather.get('forecast_temp_max_c', '-'))}"
            )
            st.markdown(
                f"**Forecast Min:** {sanitize_text(shanghai_live_weather.get('forecast_temp_min_c', '-'))}"
            )
            st.markdown(
                f"**Narrative:** {sanitize_text(shanghai_live_weather.get('forecast_narrative', '-'))}"
            )
            st.caption(
                "This forecast is extracted from the Wunderground page embed for ZSPD. "
                "Refresh is manual so the dashboard first paint is never blocked by the external site."
            )
        elif (
            realtime_forecast
            and selected_market_snapshot
            and str(realtime_forecast.get("market_id") or "")
            == str(selected_market_snapshot.get("market_id") or "")
        ):
            st.markdown(f"**Target Date:** {sanitize_text(realtime_forecast.get('target_date', '-'))}")
            st.markdown(f"**Variable:** {sanitize_text(realtime_forecast.get('variable_name', '-'))}")
            st.markdown(f"**Forecast Value:** {sanitize_text(realtime_forecast.get('value', '-'))}")
            st.markdown(f"**Model Band:** {sanitize_text(realtime_forecast.get('model_band', '-'))}")
            st.markdown(
                f"**Confidence Score:** {sanitize_text(realtime_forecast.get('confidence_score', '-'))}"
            )
            st.markdown(f"**Forecast Status:** {sanitize_text(realtime_forecast.get('source_mode', '-'))}")
        elif _is_shanghai_market(selected_market_snapshot) and shanghai_history_reference:
            st.markdown(
                f"**Reference Forecast Value:** {sanitize_text(shanghai_history_reference.get('forecast_value', '-'))}"
            )
            st.markdown(
                f"**Reference Target Date:** {sanitize_text(shanghai_history_reference.get('target_date', '-'))}"
            )
            st.caption(
                "The live forecast worker is currently tracking a different market, so this panel is showing the Shanghai reference forecast."
            )
        else:
            st.info("No future forecast snapshot is available for the selected market yet.")
