from __future__ import annotations

import weather_dashboard.ui.deb_shadow_panel as panel


def test_build_deb_shadow_panel_state_defaults() -> None:
    state = panel.build_deb_shadow_panel_state()

    assert state["summary"] is None
    assert state["runs"] == []
    assert state["diagnostics"] == []
    assert state["bundle"] is None


def test_run_rows_map_shadow_runs() -> None:
    rows = panel._run_rows(
        [
            {
                "deb_shadow_run_id": "dsr_1",
                "market_id": "m1",
                "engine_id": "deb_shadow_v1",
                "base_probability": 0.52,
                "deb_probability": 0.56,
                "bias_adjustment": 0.04,
                "calibration_gap": 0.02,
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
