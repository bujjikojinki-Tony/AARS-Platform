import pandas as pd

from weather_dashboard.ui.timeline_panel import render_timeline_panel


def test_render_timeline_panel_surfaces_top_parameter_view(monkeypatch) -> None:
    captured_metrics: list[tuple[str, object]] = []
    captured_captions: list[str] = []

    monkeypatch.setattr("weather_dashboard.ui.timeline_panel.st.subheader", lambda *args, **kwargs: None)
    monkeypatch.setattr("weather_dashboard.ui.timeline_panel.st.info", lambda *args, **kwargs: None)
    monkeypatch.setattr("weather_dashboard.ui.timeline_panel.st.caption", lambda text, **kwargs: captured_captions.append(str(text)))
    monkeypatch.setattr("weather_dashboard.ui.timeline_panel.st.metric", lambda label, value, **kwargs: captured_metrics.append((label, value)))
    monkeypatch.setattr("weather_dashboard.ui.timeline_panel.st.dataframe", lambda *args, **kwargs: None)
    monkeypatch.setattr("weather_dashboard.ui.timeline_panel.st.checkbox", lambda *args, **kwargs: False)
    monkeypatch.setattr("weather_dashboard.ui.timeline_panel.st.columns", lambda n: [_DummyCtx() for _ in range(n)])
    monkeypatch.setattr("weather_dashboard.ui.timeline_panel.st.container", lambda **kwargs: _DummyCtx())

    df = pd.DataFrame(
        [
            {
                "timestamp": "2026-04-19T09:00:00Z",
                "market_id": "m1",
                "comparison_status": "aligned",
                "band_distance": 0,
                "confidence_score": 0.9,
                "confidence_adjusted_gap": 0.08,
            }
        ]
    )

    render_timeline_panel(
        df,
        "m1",
        top_parameter_view={
            "schema_version": "top_parameter_view.v1",
            "market_family": "temperature_daily_max",
            "market_question": "Will Shanghai exceed 35C?",
            "market_id": "m1",
            "weather": {"forecast_value": 35.1, "station_id": "ZSPD"},
            "source_contract": {"source_match_grade": "exact_station", "freshness_status": "fresh"},
            "decision": {"can_execute": "yes", "primary_block_reason": "none"},
        },
    )

    assert "Top Parameter Surface" in captured_captions
    assert ("Market", "temperature_daily_max") in captured_metrics
    assert ("Weather", "35.1") in captured_metrics
    assert ("Source", "exact_station") in captured_metrics
    assert ("Decision", "yes") in captured_metrics


class _DummyCtx:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False
