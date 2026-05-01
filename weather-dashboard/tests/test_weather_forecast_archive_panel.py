from __future__ import annotations

import weather_dashboard.ui.weather_forecast_archive_panel as panel


def test_build_weather_archive_panel_state_defaults() -> None:
    state = panel.build_weather_archive_panel_state()

    assert state["summary"] is None
    assert state["forecasts"] == []
    assert state["evidence"] == []
    assert state["weather_views"] == []
    assert state["bundle"] is None
    assert state["warnings"] == []


def test_forecast_rows_maps_archive_items() -> None:
    rows = panel._forecast_rows(
        [
            {
                "forecast_archive_id": "wfa_1",
                "market_id": "m1",
                "source_id": "openmeteo_tokyo",
                "source_type": "OPEN_METEO",
                "metric": "temperature_high",
                "unit": "C",
                "expected_value": 31.2,
                "sigma": 1.4,
                "archived_at": "2026-04-30T00:00:00Z",
                "archive_reason": "PROBABILITY_BUILD_CAPTURE",
            }
        ]
    )

    assert rows[0]["market_id"] == "m1"
    assert rows[0]["source_type"] == "OPEN_METEO"


def test_bundle_summary_includes_counts() -> None:
    text = panel._bundle_summary(
        {
            "market_id": "m1",
            "forecasts": [{}],
            "evidence": [{}, {}],
            "weather_views": [{}],
        }
    )

    assert "m1" in text
    assert "1 forecasts" in text
    assert "2 evidence records" in text
