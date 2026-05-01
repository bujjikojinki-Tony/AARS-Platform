from __future__ import annotations

import weather_dashboard.ui.emos_shadow_panel as panel


def test_build_emos_shadow_panel_state_defaults() -> None:
    state = panel.build_emos_shadow_panel_state()

    assert state["summary"] is None
    assert state["runs"] == []
    assert state["diagnostics"] == []
    assert state["bundle"] is None


def test_run_rows_map_shadow_runs() -> None:
    rows = panel._run_rows(
        [
            {
                "emos_shadow_run_id": "esr_1",
                "market_id": "m1",
                "engine_id": "emos_shadow_v1",
                "base_probability": 0.52,
                "emos_probability": 0.54,
                "location_adjustment": 0.01,
                "scale_adjustment": 0.01,
                "sample_count": 4,
                "run_status": "READY",
                "created_at": "2026-05-01T00:00:00Z",
            }
        ]
    )

    assert rows[0]["market_id"] == "m1"
    assert rows[0]["run_status"] == "READY"


def test_bundle_summary_includes_counts() -> None:
    text = panel._bundle_summary(
        {
            "market_id": "m1",
            "runs": [{}],
            "diagnostics": [{}, {}],
        }
    )

    assert "m1" in text
    assert "1 shadow runs" in text
    assert "2 diagnostics" in text
