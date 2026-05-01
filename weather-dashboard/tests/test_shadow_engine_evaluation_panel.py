from __future__ import annotations

import weather_dashboard.ui.shadow_engine_evaluation_panel as panel


def test_build_shadow_engine_evaluation_panel_state_defaults() -> None:
    state = panel.build_shadow_engine_evaluation_panel_state()

    assert state["summary"] is None
    assert state["evaluations"] == []
    assert state["bundle"] is None


def test_evaluation_rows_map_records() -> None:
    rows = panel._evaluation_rows(
        [
            {
                "shadow_evaluation_id": "see_1",
                "market_id": "m1",
                "primary_probability": 0.60,
                "deb_probability": 0.61,
                "emos_probability": 0.58,
                "actual_outcome_value": 1.0,
                "primary_brier_score": 0.16,
                "deb_brier_score": 0.1521,
                "emos_brier_score": 0.1764,
                "best_engine": "DEB_SHADOW",
                "evaluation_status": "READY",
                "created_at": "2026-05-01T00:00:00Z",
            }
        ]
    )

    assert rows[0]["market_id"] == "m1"
    assert rows[0]["best_engine"] == "DEB_SHADOW"


def test_bundle_summary_includes_counts() -> None:
    text = panel._bundle_summary(
        {
            "market_id": "m1",
            "evaluations": [{}, {}],
        }
    )

    assert "m1" in text
    assert "2 evaluation rows" in text
