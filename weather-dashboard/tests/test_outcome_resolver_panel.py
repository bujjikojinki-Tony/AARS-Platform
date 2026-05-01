from __future__ import annotations

import weather_dashboard.ui.outcome_resolver_panel as panel


def test_build_outcome_panel_state_defaults() -> None:
    state = panel.build_outcome_panel_state()

    assert state["summary"] is None
    assert state["markets"] == []
    assert state["weather_actuals"] == []
    assert state["resolutions"] == []
    assert state["bundle"] is None


def test_market_rows_maps_records() -> None:
    rows = panel._market_rows(
        [
            {
                "market_outcome_id": "mor_1",
                "market_id": "m1",
                "source": "MANUAL",
                "resolved_outcome": "YES",
                "resolution_status": "RESOLVED",
                "resolved_at": "2026-04-30T00:00:00Z",
                "resolved_value": 31.2,
            }
        ]
    )

    assert rows[0]["market_id"] == "m1"
    assert rows[0]["resolved_outcome"] == "YES"


def test_resolution_rows_include_threshold_and_status() -> None:
    rows = panel._resolution_rows(
        [
            {
                "outcome_resolution_id": "orr_1",
                "market_id": "m1",
                "weather_actual_id": "war_1",
                "direction": "ABOVE",
                "actual_value": 31.2,
                "threshold": 30.0,
                "resolved_outcome": "YES",
                "resolution_status": "RESOLVED",
                "resolution_source": "WEATHER_ACTUAL",
                "resolved_at": "2026-04-30T00:00:00Z",
            }
        ]
    )

    assert rows[0]["threshold"] == 30.0
    assert rows[0]["resolution_status"] == "RESOLVED"
