import pandas as pd

from weather_dashboard.ui import comparison_table


def test_render_comparison_table_surfaces_top_parameter_view(monkeypatch) -> None:
    captured_metrics: list[tuple[str, object]] = []
    captured_captions: list[str] = []

    monkeypatch.setattr(comparison_table.st, "subheader", lambda *args, **kwargs: None)
    monkeypatch.setattr(comparison_table.st, "info", lambda *args, **kwargs: None)
    monkeypatch.setattr(comparison_table.st, "dataframe", lambda *args, **kwargs: None)
    monkeypatch.setattr(comparison_table.st, "metric", lambda label, value, **kwargs: captured_metrics.append((label, value)))
    monkeypatch.setattr(comparison_table.st, "caption", lambda text, **kwargs: captured_captions.append(str(text)))
    monkeypatch.setattr(comparison_table.st, "columns", lambda n: [_DummyCtx() for _ in range(n)])
    monkeypatch.setattr(comparison_table.st, "container", lambda **kwargs: _DummyCtx())

    df = pd.DataFrame(
        [
            {
                "market_id": "m1",
                "top_parameter_view": {
                    "schema_version": "top_parameter_view.v1",
                    "market_family": "temperature_daily_max",
                    "market_question": "Will Shanghai exceed 35C?",
                    "market_id": "m1",
                    "weather": {"forecast_value": 35.1, "station_id": "ZSPD"},
                    "source_contract": {"source_match_grade": "exact_station", "freshness_status": "fresh"},
                    "decision": {"can_execute": "yes", "primary_block_reason": "none"},
                },
            }
        ]
    )

    comparison_table.render_comparison_table(df)

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
