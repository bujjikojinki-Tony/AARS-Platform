import pandas as pd

from weather_dashboard.ui.market_evidence_chart import render_market_evidence_chart


def test_render_market_evidence_chart_surfaces_top_parameter_view(monkeypatch) -> None:
    captured_metrics: list[tuple[str, object]] = []
    captured_captions: list[str] = []

    monkeypatch.setattr("weather_dashboard.ui.market_evidence_chart.st.subheader", lambda *args, **kwargs: None)
    monkeypatch.setattr("weather_dashboard.ui.market_evidence_chart.st.caption", lambda text, **kwargs: captured_captions.append(str(text)))
    monkeypatch.setattr("weather_dashboard.ui.market_evidence_chart.st.metric", lambda label, value, **kwargs: captured_metrics.append((label, value)))
    monkeypatch.setattr("weather_dashboard.ui.market_evidence_chart.st.info", lambda *args, **kwargs: None)
    monkeypatch.setattr("weather_dashboard.ui.market_evidence_chart.st.markdown", lambda *args, **kwargs: None)
    monkeypatch.setattr("weather_dashboard.ui.market_evidence_chart.st.line_chart", lambda *args, **kwargs: None)
    monkeypatch.setattr("weather_dashboard.ui.market_evidence_chart.st.dataframe", lambda *args, **kwargs: None)
    monkeypatch.setattr("weather_dashboard.ui.market_evidence_chart.st.expander", lambda *args, **kwargs: _DummyCtx())
    monkeypatch.setattr(
        "weather_dashboard.ui.market_evidence_chart.st.columns",
        lambda n: [_DummyCol() for _ in range(len(n) if isinstance(n, list) else n)],
    )
    monkeypatch.setattr("weather_dashboard.ui.market_evidence_chart.st.container", lambda **kwargs: _DummyCtx())

    training_samples_df = pd.DataFrame(
        [
            {
                "market_id": "m1",
                "timestamp": "2026-04-19T09:00:00Z",
                "market_probability": 0.61,
                "yes_price": 0.62,
                "model_probability": 0.7,
                "fair_value": 0.71,
                "model_value": 35.1,
                "official_value": 35.0,
                "is_labeled": True,
            }
        ]
    )

    render_market_evidence_chart(
        training_samples_df,
        "m1",
        [],
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
    assert any(label == "Weather" and str(value).startswith("35.1") for label, value in captured_metrics)
    assert ("Source", "exact_station") in captured_metrics
    assert ("Decision", "yes") in captured_metrics


class _DummyCtx:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _DummyCol(_DummyCtx):
    def metric(self, *args, **kwargs):
        return None
